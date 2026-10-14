import json
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/readiness"))
import measure


def active_process(pid):
    result = subprocess.run(["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() and not result.stdout.strip().startswith("Z")


class TimingBoundaryTests(unittest.TestCase):
    def test_timeout_retains_real_partial_output_and_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            output, log = Path(directory) / "timings.json", Path(directory) / "trace.log"
            status = measure.run("trace", [sys.executable, "-c",
                "import time; print('trace started', flush=True); time.sleep(20)"],
                output, timeout_seconds=0.3, log_path=log)
            self.assertEqual(status, 124)
            record = json.loads(output.read_text())[0]
            self.assertEqual(record["status"], "timed_out")
            self.assertEqual(record["exit_code"], 124)
            self.assertLess(record["duration_seconds"], 5)
            self.assertIn("trace started", log.read_text())

    def test_failed_command_retains_stderr_and_original_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            output, log = Path(directory) / "timings.json", Path(directory) / "trace.log"
            status = measure.run("trace", [sys.executable, "-c",
                "import sys; print('compiler failure', file=sys.stderr); sys.exit(7)"],
                output, timeout_seconds=5, log_path=log)
            self.assertEqual(status, 7)
            self.assertEqual(json.loads(output.read_text())[0]["status"], "failed")
            self.assertIn("compiler failure", log.read_text())

    def test_timeout_terminates_owned_children_even_when_they_ignore_sigterm(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child_file = root / "child.pid"
            child_code = (
                "import os, pathlib, signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                f"pathlib.Path({str(child_file)!r}).write_text(str(os.getpid())); time.sleep(20)"
            )
            parent_code = (
                f"import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {child_code!r}]); "
                "time.sleep(20)"
            )
            status = measure.run("trace", [sys.executable, "-c", parent_code],
                                 root / "timings.json", timeout_seconds=0.5, log_path=root / "trace.log")
            self.assertEqual(status, 124)
            self.assertTrue(child_file.exists())
            pid = int(child_file.read_text())
            deadline = time.monotonic() + 2
            while active_process(pid) and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertFalse(active_process(pid), "Owned compiler descendant survived timeout cleanup")

    def test_interruption_records_state_and_retains_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ready, output, log = root / "ready", root / "timings.json", root / "trace.log"
            child_code = (
                "import pathlib, time; print('trace started', flush=True); "
                f"pathlib.Path({str(ready)!r}).write_text('ready'); time.sleep(20)"
            )
            process = subprocess.Popen([
                sys.executable, str(ROOT / "tools/readiness/measure.py"),
                "--name", "trace", "--output", str(output), "--timeout-seconds", "20",
                "--log", str(log), "--", sys.executable, "-c", child_code,
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                deadline = time.monotonic() + 3
                while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(ready.exists(), process.communicate(timeout=1)[0] if process.poll() is not None else "Child did not start")
                running = json.loads(output.read_text())[0]
                self.assertEqual(running["status"], "running")
                self.assertIsNone(running["exit_code"])
                process.send_signal(signal.SIGTERM)
                process.communicate(timeout=5)
                self.assertEqual(process.returncode, 128 + signal.SIGTERM)
                record = json.loads(output.read_text())[0]
                self.assertEqual(record["status"], "interrupted")
                self.assertIn("trace started", log.read_text())
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()

    def test_invalid_timeout_is_rejected_before_starting_a_command(self):
        with tempfile.TemporaryDirectory() as directory:
            for value in (0, -1, float("nan"), float("inf")):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    measure.run("trace", [sys.executable, "-c", "pass"],
                                Path(directory) / "timings.json", timeout_seconds=value)

    def test_stale_log_is_preserved_instead_of_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "trace.log"
            log.write_text("previous failed trace")
            with self.assertRaises(FileExistsError):
                measure.run("trace", [sys.executable, "-c", "pass"],
                            root / "timings.json", timeout_seconds=1, log_path=log)
            self.assertEqual(log.read_text(), "previous failed trace")
            self.assertFalse((root / "timings.json").exists())


if __name__ == "__main__":
    unittest.main()
