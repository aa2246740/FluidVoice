import datetime
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/readiness"))
import check


class DebtContractTests(unittest.TestCase):
    def fixture(self, directory, text="// TODO: repair boundary\n"):
        root = Path(directory)
        source = root / "Sources/Fluid/Example.swift"
        source.parent.mkdir(parents=True)
        source.write_text(text)
        entry = {
            "file": "Sources/Fluid/Example.swift",
            "marker": "TODO: repair boundary",
            "owner": "@maintainer",
            "issue": "https://github.com/example/project/issues/7",
            "review_by": "2026-11-13",
            "resolution": "Add a regression and repair the boundary.",
        }
        return root, source, {"technical_debt": [entry]}

    def test_real_comments_are_scanned_and_literals_are_not(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, _ = self.fixture(directory, '''// TODO: real line
/*
 FIXME: real block
 /* nested block */
 HACK: outer block after nested close
*/
let normal = "https://example.test // TODO: literal"
let multiline = """
// FIXME: multiline literal
"""
let raw = #"quoted " // TODO: raw literal"#
let rawMultiline = #"""
/* HACK: raw multiline literal */
"""#
''')
            debt = check.debt_inventory(root)
            self.assertEqual([item["marker"] for item in debt], [
                "TODO: real line", "FIXME: real block", "HACK: outer block after nested close",
            ])
            self.assertEqual([item["line"] for item in debt], [1, 3, 5])

    def test_registration_tracks_owner_issue_and_location_without_line_pinning(self):
        with tempfile.TemporaryDirectory() as directory:
            root, source, policy = self.fixture(directory)
            source.write_text("\n\n" + source.read_text())
            report = check.verify_debt(root, policy, datetime.date(2026, 10, 14))
            self.assertEqual(report[0]["line"], 3)
            self.assertEqual(report[0]["owner"], "@maintainer")
            self.assertEqual(report[0]["issue"], policy["technical_debt"][0]["issue"])
            self.assertTrue(report[0]["linked_issue"])

    def test_unregistered_and_copied_markers_fail_the_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root, source, policy = self.fixture(directory)
            source.write_text(source.read_text() + "// FIXME: additional debt\n")
            with self.assertRaisesRegex(ValueError, "Unregistered technical debt"):
                check.verify_debt(root, policy, datetime.date(2026, 10, 14))
            source.write_text("// TODO: repair boundary\n" * 2)
            with self.assertRaisesRegex(ValueError, "Unregistered technical debt"):
                check.verify_debt(root, policy, datetime.date(2026, 10, 14))

    def test_deleted_debt_requires_removing_its_stale_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            root, source, policy = self.fixture(directory)
            source.write_text("let repaired = true\n")
            with self.assertRaisesRegex(ValueError, "Stale debt policy"):
                check.verify_debt(root, policy, datetime.date(2026, 10, 14))

    def test_registration_requires_owner_issue_resolution_and_review_date(self):
        for key, value in (
            ("owner", ""), ("issue", "PR #950"), ("resolution", ""),
            ("review_by", "not-a-date"), ("review_by", "2026-10-14"),
        ):
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as directory:
                root, _, policy = self.fixture(directory)
                policy["technical_debt"][0][key] = value
                with self.assertRaises(ValueError):
                    check.verify_debt(root, policy, datetime.date(2026, 10, 14))

    def test_duplicate_registration_cannot_hide_multiple_occurrences(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, policy = self.fixture(directory)
            policy["technical_debt"].append(dict(policy["technical_debt"][0]))
            with self.assertRaisesRegex(ValueError, "Duplicate debt policy"):
                check.verify_debt(root, policy, datetime.date(2026, 10, 14))

    def test_existing_repository_debt_has_real_fork_work_item_and_owner(self):
        policy = json.loads((ROOT / "tools/readiness/policies.json").read_text())
        report = check.verify_debt(ROOT, policy, datetime.date(2026, 10, 14))
        self.assertEqual(len(report), 5)
        for item in report:
            self.assertEqual(item["issue"], "https://github.com/aa2246740/FluidVoice/issues/7")
            self.assertEqual(item["owner"], "@aa2246740")
            self.assertTrue(item["linked_issue"])


if __name__ == "__main__":
    unittest.main()
