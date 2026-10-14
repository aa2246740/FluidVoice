import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class SecurityWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = (ROOT / ".github/workflows/security-review.yml").read_text()

    def test_cold_trace_has_its_own_deadline_and_retained_log(self):
        trace = self.workflow.split("name: Trace the public application build", 1)[1]
        trace = trace.split("github/codeql-action/analyze", 1)[0]
        self.assertIn("tools/readiness/measure.py", trace)
        self.assertIn("--timeout-seconds 1800", trace)
        self.assertIn("--log quality-artifacts/security/xcodebuild.log", trace)
        self.assertIn("--output quality-artifacts/security/timings.json", trace)
        self.assertNotIn("continue-on-error", self.workflow)

    def test_single_initialization_explicitly_selects_swift_manual_tracing(self):
        self.assertEqual(self.workflow.count("github/codeql-action/init@"), 1)
        initialization = self.workflow.split("name: Initialize Swift compiler tracing", 1)[1]
        initialization = initialization.split("name: Trace the public application build", 1)[0]
        self.assertIn("languages: swift", initialization)
        self.assertIn("build-mode: manual", initialization)
        self.assertRegex(initialization, r"timeout-minutes:\s*5")

    def test_packages_are_saved_before_tracing_without_caching_build_products(self):
        restore = self.workflow.index("actions/cache/restore@v4")
        resolve = self.workflow.index("name: Resolve pinned packages")
        save = self.workflow.index("actions/cache/save@v4")
        initialize = self.workflow.index("github/codeql-action/init")
        trace = self.workflow.index("name: Trace the public application build")
        self.assertLess(restore, resolve)
        self.assertLess(resolve, save)
        self.assertLess(save, initialize)
        self.assertLess(initialize, trace)
        self.assertEqual(self.workflow.count("DerivedData-Security"), 1)
        self.assertIn("runner.os", self.workflow)
        self.assertIn("steps.toolchain.outputs.version", self.workflow)

    def test_job_budget_reserves_time_for_analysis_and_evidence(self):
        budgets = [int(value) for value in re.findall(r"timeout-minutes:\s*(\d+)", self.workflow)]
        self.assertGreaterEqual(budgets[0], 50)
        self.assertIn("name: Analyze traced Swift sources", self.workflow)
        analysis = self.workflow.split("name: Analyze traced Swift sources", 1)[1]
        self.assertRegex(analysis.split("with:", 1)[0], r"timeout-minutes:\s*10")
        self.assertIn("--timeout-seconds 300", self.workflow)

    def test_failed_trace_preserves_more_than_an_absent_sarif_directory(self):
        artifact = self.workflow.split("name: Preserve security diagnostics and assessments", 1)[1]
        self.assertIn("if: always()", artifact)
        self.assertIn("path: quality-artifacts/security/", artifact)
        self.assertIn("if-no-files-found: error", artifact)
        self.assertIn("quality-artifacts/security/toolchain.log", self.workflow)
        self.assertIn("quality-artifacts/security/provenance.txt", self.workflow)


if __name__ == "__main__":
    unittest.main()
