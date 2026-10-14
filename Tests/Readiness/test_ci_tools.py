import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools/readiness" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


changes = load("changes")
measure = load("measure")


class ChangeDetectionTests(unittest.TestCase):
    def test_native_inputs(self):
        for path in (
            "Sources/CoreAudioCaptureSupport/capture.c", "Sources/Fluid/App.swift",
            "Vendor/WebRTCAudioProcessing/Package.swift", "Tests/CloudASRClientTests.swift",
            "Fluid.xcodeproj/project.pbxproj", "Package.resolved", "build.sh",
        ):
            with self.subTest(path=path):
                self.assertTrue(changes.relevant(path))

    def test_documentation_and_tool_tests_do_not_need_xcode(self):
        for path in ("README.md", "docs/readiness/runbooks.md", "Tests/Readiness/test_ci_tools.py"):
            self.assertFalse(changes.relevant(path))

    def test_git_diff_covers_a_multi_commit_push_and_unusual_paths(self):
        before = "a" * 40
        with patch.object(changes, "git", side_effect=[b"", b"Sources/line\nbreak.swift\0README.md\0"]) as git:
            result = changes.detect(ROOT, "push", {"before": before})
        self.assertTrue(result["relevant"])
        self.assertIn("Sources/line\nbreak.swift", result["files"])
        self.assertEqual(git.call_args.args, (ROOT, "diff", "--name-only", "-z", before, "HEAD"))

    def test_pr_merge_diff_includes_all_feature_commits(self):
        with patch.object(changes, "git", return_value=b"Sources/change.swift\0notes.txt\0") as git:
            self.assertTrue(changes.detect(ROOT, "pull_request", {})["relevant"])
        self.assertEqual(git.call_args.args, (ROOT, "diff", "--name-only", "-z", "HEAD^1", "HEAD"))

    def test_new_branch_scans_tracked_files(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.git(repo, "init", "-q", "--initial-branch=main")
            path = repo / "Sources/line\nbreak.swift"
            path.parent.mkdir()
            path.write_text("app")
            self.git(repo, "add", "--", "Sources/line\nbreak.swift")
            self.assertTrue(changes.detect(repo, "push", {"before": "0" * 40})["relevant"])

    @staticmethod
    def git(repo, *args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True)


class TimingTests(unittest.TestCase):
    def test_records_success_and_failure_without_hiding_exit_status(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "timings.json"
            self.assertEqual(measure.run("success", [sys.executable, "-c", "pass"], output), 0)
            self.assertEqual(measure.run("failure", [sys.executable, "-c", "raise SystemExit(7)"], output), 7)
            records = json.loads(output.read_text())
            self.assertEqual([item["exit_code"] for item in records], [0, 7])
            self.assertTrue(all(item["duration_seconds"] >= 0 for item in records))
            self.assertTrue(all(item["started_at"].endswith("+00:00") for item in records))

    def test_missing_command_is_recorded_as_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "timings.json"
            self.assertEqual(measure.run("missing", ["/nonexistent/fluidvoice-command"], output), 127)
            self.assertEqual(json.loads(output.read_text())[0]["exit_code"], 127)

    def test_empty_command_is_rejected(self):
        with self.assertRaises(ValueError):
            measure.run("empty", [], Path("/unused"))


if __name__ == "__main__":
    unittest.main()
