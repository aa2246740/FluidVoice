"""Deterministic timeout and process-ownership regressions for the native watchdog."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("native_diagnostics", ROOT / "tools/readiness/native_diagnostics.py")
diagnostics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostics)


class NativeDiagnosticTests(unittest.TestCase):
    def test_slow_case_is_captured_once_before_test_timeout(self):
        progress = diagnostics.TestProgress(90)
        progress.feed("Test Case '-[ASRScopeTests testTranscribe]' started.", 1)
        self.assertEqual(progress.due(90), [])
        self.assertEqual(progress.due(91), [("-[ASRScopeTests testTranscribe]", 1, 90)])
        self.assertEqual(progress.due(120), [])

    def test_completed_case_does_not_generate_a_hang_sample(self):
        progress = diagnostics.TestProgress(90)
        progress.feed("Test Case '-[ScopeTests testSuccess]' started.", 0)
        progress.feed("Test Case '-[ScopeTests testSuccess]' passed (0.001 seconds).", 1)
        self.assertEqual(progress.due(100), [])
        progress.feed("Test Case '-[ScopeTests testFailure]' started.", 101)
        progress.feed("Test Case '-[ScopeTests testFailure]' failed (0.002 seconds).", 102)
        self.assertEqual(progress.due(200), [])

    def test_only_app_processes_from_exact_derived_data_are_sampled(self):
        derived = Path("/tmp/fixture/DerivedData")
        listing = (
            "10 /tmp/fixture/DerivedData/Build/Products/Debug/FluidVoice Debug.app/Contents/MacOS/FluidVoice Debug\n"
            "11 /tmp/fixture/DerivedData-other/FluidVoice.app/Contents/MacOS/FluidVoice\n"
            "12 /Applications/Unrelated.app/Contents/MacOS/Unrelated\n"
            "13 /tmp/fixture/DerivedData/Build/Products/Debug/FluidASRBaselineHost.app/Contents/MacOS/FluidASRBaselineHost\n"
            "14 /usr/bin/xcodebuild\n"
        )
        self.assertEqual(diagnostics.owned_processes(listing, derived),
                         [(10, "FluidVoice Debug"), (13, "FluidASRBaselineHost")])

    def test_sampling_failure_is_retained_without_exposing_process_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            derived = output / "DerivedData"
            listing = f"42 {derived}/Debug/FluidVoice Debug.app/Contents/MacOS/FluidVoice Debug\n"
            with patch.object(diagnostics.subprocess, "check_output", return_value=listing), \
                 patch.object(diagnostics.subprocess, "run",
                              return_value=subprocess.CompletedProcess([], 1, "", "private arguments")):
                diagnostics.capture("testFixture", 1, 90, output, derived)
            report = json.loads((output / "test-1.json").read_text())
            self.assertEqual(report["processes"][0]["exit_code"], 1)
            self.assertIsNone(report["processes"][0]["stack_file"])
            self.assertNotIn("private arguments", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
