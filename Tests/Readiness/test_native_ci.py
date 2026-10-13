"""Exercise native CI control flow without Xcode, real models or network access."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import textwrap
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("artifact_metadata", ROOT / "tools/readiness/artifact_metadata.py")
artifact_metadata = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artifact_metadata)


class MetadataTests(unittest.TestCase):
    def test_rejects_invalid_test_results_and_dirty_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "app.zip"
            archive.write_bytes(b"fake application archive")
            for status, code in (("unknown", None), ("not_run", 0), ("passed", 65),
                                 ("failed", 0), ("interrupted", None)):
                with self.subTest(status=status, code=code), self.assertRaises(ValueError):
                    artifact_metadata.record(archive, status, code)
            with patch.object(artifact_metadata.subprocess, "check_output", return_value=" M Package.resolved"):
                with self.assertRaisesRegex(ValueError, "Tracked source or pins"):
                    artifact_metadata.record(archive, "not_run", None)

    def test_archive_hash_and_status_remain_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "app.zip"
            archive.write_bytes(b"fake application archive")
            with patch.object(artifact_metadata.subprocess, "check_output",
                              side_effect=["", "f" * 40, "Xcode fixture"]):
                result = artifact_metadata.record(archive, "interrupted", 143)
            self.assertEqual(result["test_status"], "interrupted")
            self.assertEqual(result["test_exit_code"], 143)
            self.assertEqual(result["sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertFalse(result["working_tree_dirty"])


class NativeCIFlowTests(unittest.TestCase):
    script_under_test = (ROOT / "tools/readiness/native_ci.sh").read_text()

    def run_fixture(self, build_code=0, test_code=0, tee_code=0, interrupt=False, stale=False):
        with tempfile.TemporaryDirectory(prefix="fluidvoice-native-fixture-") as directory:
            root = Path(directory)
            tools = root / "tools/readiness"
            tools.mkdir(parents=True)
            for name in ("measure.py", "bundle_size.py", "artifact_metadata.py", "native_diagnostics.py"):
                shutil.copyfile(ROOT / "tools/readiness" / name, tools / name)
            (tools / "check.py").write_text("print('fixture repository checks')\n")
            script = tools / "native_ci.sh"
            script.write_text(self.script_under_test)
            if stale:
                artifacts = root / "quality-artifacts"
                artifacts.mkdir()
                (artifacts / "FluidVoice-unsigned.zip").write_bytes(b"old archive")
                (artifacts / "build-metadata.json").write_text(json.dumps({"test_status": "passed", "commit": "old"}))
            binaries = root / "bin"
            binaries.mkdir()
            commands = {
                "xcodebuild": """
                    import json,os,pathlib,signal,sys
                    root=pathlib.Path.cwd()
                    if sys.argv[1] == "-version":
                        print("Xcode fixture")
                    elif sys.argv[1] == "build-for-testing":
                        code=int(os.environ["BUILD_EXIT_CODE"])
                        if not code:
                            app=root/"DerivedData/Build/Products/Debug/FluidVoice Debug.app"
                            app.mkdir(parents=True)
                            (app/"fake-executable").write_bytes(b"not a real executable")
                        sys.exit(code)
                    elif sys.argv[1] == "test-without-building":
                        metadata=json.loads((root/"quality-artifacts/build-metadata.json").read_text())
                        assert metadata["test_status"] == "not_run"
                        assert (root/"quality-artifacts/FluidVoice-unsigned.zip").is_file()
                        assert "-test-timeouts-enabled" in sys.argv
                        assert sys.argv[sys.argv.index("-maximum-test-execution-time-allowance")+1] == "180"
                        skips=[item for item in sys.argv if item.startswith("-skip-testing:")]
                        assert skips == ["-skip-testing:FluidDictationIntegrationTests/DictationE2ETests/testDictationEndToEnd_whisperTiny_transcribesFixture"]
                        (root/"test-started").touch()
                        if os.environ["INTERRUPT_TEST"] == "1":
                            signal.pause()
                        sys.exit(int(os.environ["TEST_EXIT_CODE"]))
                    elif sys.argv[1] == "test":
                        # The former combined action builds, then fails before packaging.
                        app=root/"DerivedData/Build/Products/Debug/FluidVoice Debug.app"
                        app.mkdir(parents=True)
                        (app/"fake-executable").write_bytes(b"not a real executable")
                        (root/"test-started").touch()
                        sys.exit(int(os.environ["TEST_EXIT_CODE"]))
                    else:
                        raise AssertionError("Unexpected Xcode action")
                """,
                "git": """
                    import sys
                    print("f"*40 if "rev-parse" in sys.argv else "")
                """,
                "ditto": """
                    import pathlib,sys
                    pathlib.Path(sys.argv[-1]).write_bytes(b"fake unsigned archive")
                """,
                "xcrun": """
                    print('{"fixture_coverage": true}')
                """,
                "tee": """
                    import os,pathlib,sys
                    data=sys.stdin.buffer.read()
                    path=pathlib.Path(sys.argv[-1])
                    with path.open("ab" if "-a" in sys.argv else "wb") as target:
                        target.write(data)
                    sys.stdout.buffer.write(data)
                    sys.exit(int(os.environ["TEE_EXIT_CODE"]) if "-a" in sys.argv else 0)
                """,
            }
            for name, code in commands.items():
                path = binaries / name
                path.write_text("#!/usr/bin/env python3\n" + textwrap.dedent(code).lstrip())
                path.chmod(0o755)
            environment = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ["PATH"],
                               BUILD_EXIT_CODE=str(build_code), TEST_EXIT_CODE=str(test_code),
                               TEE_EXIT_CODE=str(tee_code), INTERRUPT_TEST="1" if interrupt else "0")
            environment.pop("GITHUB_STEP_SUMMARY", None)
            with subprocess.Popen(["/bin/bash", str(script)], env=environment, start_new_session=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
                try:
                    if interrupt:
                        deadline = time.monotonic() + 8
                        while not (root / "test-started").exists() and time.monotonic() < deadline:
                            if process.poll() is not None:
                                break
                            time.sleep(0.02)
                        self.assertTrue((root / "test-started").exists())
                        os.killpg(process.pid, signal.SIGTERM)
                    output, errors = process.communicate(timeout=15)
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.communicate()
            artifacts = root / "quality-artifacts"
            metadata = artifacts / "build-metadata.json"
            return {
                "code": process.returncode, "output": output + errors,
                "metadata": json.loads(metadata.read_text()) if metadata.exists() else None,
                "archive": (artifacts / "FluidVoice-unsigned.zip").exists(),
                "tests_started": (root / "test-started").exists(),
                "coverage": (artifacts / "app-coverage.json").exists(),
            }

    def test_success_saves_unverified_artifact_before_testing(self):
        result = self.run_fixture()
        self.assertEqual(result["code"], 0, result["output"])
        self.assertTrue(result["tests_started"])
        self.assertEqual(result["metadata"]["test_status"], "passed")
        self.assertEqual(result["metadata"]["test_exit_code"], 0)
        self.assertTrue(result["coverage"])

    def test_failed_tests_retain_artifact_and_fail_gate(self):
        result = self.run_fixture(test_code=65)
        self.assertEqual(result["code"], 65, result["output"])
        self.assertTrue(result["archive"])
        self.assertTrue(result["tests_started"])
        self.assertEqual(result["metadata"]["test_status"], "failed")
        self.assertEqual(result["metadata"]["test_exit_code"], 65)
        self.assertFalse(result["coverage"])

    def test_build_failure_does_not_package_or_start_tests(self):
        result = self.run_fixture(build_code=65)
        self.assertEqual(result["code"], 65, result["output"])
        self.assertFalse(result["archive"])
        self.assertFalse(result["tests_started"])
        self.assertIsNone(result["metadata"])

    def test_log_capture_failure_cannot_pass_gate(self):
        result = self.run_fixture(tee_code=1)
        self.assertEqual(result["code"], 1, result["output"])
        self.assertEqual(result["metadata"]["test_status"], "passed")
        self.assertFalse(result["coverage"])

    def test_interruption_retains_artifact_without_claiming_test_success(self):
        result = self.run_fixture(interrupt=True)
        self.assertEqual(result["code"], 143, result["output"])
        self.assertTrue(result["archive"])
        self.assertEqual(result["metadata"]["test_status"], "interrupted")
        self.assertEqual(result["metadata"]["test_exit_code"], 143)
        self.assertFalse(result["coverage"])

    def test_stale_evidence_is_not_overwritten_or_reused(self):
        result = self.run_fixture(stale=True)
        self.assertEqual(result["code"], 1, result["output"])
        self.assertIn("Native evidence already exists", result["output"])
        self.assertFalse(result["tests_started"])
        self.assertEqual(result["metadata"], {"test_status": "passed", "commit": "old"})


if __name__ == "__main__":
    unittest.main()
