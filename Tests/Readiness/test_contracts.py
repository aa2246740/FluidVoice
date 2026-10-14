import datetime
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/readiness"))
import check
import duplicates
import bundle_size
import standalone
import sync_pins


class DependencyDriftTests(unittest.TestCase):
    def test_sync_keeps_app_and_root_only_pins_intact(self):
        root = {"pins": [{"identity": "shared", "state": {"version": "old"}}, {"identity": "root-only", "state": {"revision": "keep"}}]}
        app = {"pins": [{"identity": "shared", "state": {"version": "canonical"}}]}
        original = json.dumps(app)
        self.assertEqual(sync_pins.synchronize(root, app), ["shared"])
        self.assertEqual(root["pins"][0]["state"]["version"], "canonical")
        self.assertEqual(root["pins"][1]["state"], {"revision": "keep"})
        self.assertEqual(json.dumps(app), original)

    def fixture(self, root, state):
        pin = {"identity": "shared", "state": state}
        (root / "Package.resolved").write_text(json.dumps({"pins": [pin]}))
        nested = root / "Sibling"
        nested.mkdir()
        (nested / "Package.resolved").write_text(json.dumps({"pins": [pin]}))

    def test_shared_graphs_must_have_identical_versions_and_revisions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root, {"revision": "a", "version": "1.0"})
            self.assertEqual(len(check.verify_pins(root)["graphs"]), 2)
            (root / "Sibling/Package.resolved").write_text(json.dumps({
                "pins": [{"identity": "shared", "state": {"revision": "b", "version": "1.0"}}]
            }))
            with self.assertRaisesRegex(ValueError, "Dependency drift"):
                check.verify_pins(root)

    def test_missing_graph_is_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                check.verify_pins(Path(directory))


class ArchitectureTests(unittest.TestCase):
    def test_core_rejects_ui_and_app_singletons_but_not_comments_or_strings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "Core.swift"
            policy = {"core_files": ["Core.swift"], "forbidden_core_imports": ["SwiftUI"],
                      "forbidden_core_types": ["AppServices"]}
            path.write_text('import Foundation\n// import SwiftUI\nlet text = "AppServices"')
            check.verify_layers(root, policy)
            path.write_text("import SwiftUI")
            with self.assertRaises(ValueError):
                check.verify_layers(root, policy)
            path.write_text("let service = AppServices.shared")
            with self.assertRaises(ValueError):
                check.verify_layers(root, policy)

    def test_test_roles_are_explicit_and_bad_names_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tests = root / "Tests"
            tests.mkdir()
            (tests / "UsefulTests.swift").write_text("test")
            (tests / "UsefulDoubles.swift").write_text("double")
            check.verify_test_names(root)
            (tests / "mystery.swift").write_text("test")
            with self.assertRaises(ValueError):
                check.verify_test_names(root)

    def test_flags_reject_missing_usage_and_expired_review_dates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "flag.swift").write_text('let symbol = "FEATURE_KEY"\nuse(symbol)')
            policy = {"temporary_flags": [{"key": "FEATURE_KEY", "symbol": "symbol", "file": "flag.swift",
                                          "owner": "@owner", "review_by": "2026-11-01", "removal_condition": "validation"}]}
            check.verify_flags(root, policy, datetime.date(2026, 10, 12))
            with self.assertRaises(ValueError):
                check.verify_flags(root, policy, datetime.date(2026, 11, 1))
            (root / "flag.swift").write_text('let symbol = "FEATURE_KEY"')
            with self.assertRaises(ValueError):
                check.verify_flags(root, policy, datetime.date(2026, 10, 12))


class DocumentationTests(unittest.TestCase):
    def test_every_reference_resolves_and_remote_refs_are_rejected(self):
        check.validate_refs({"components": {"schemas": {"Thing": {}}}, "$ref": "#/components/schemas/Thing"})
        with self.assertRaises(KeyError):
            check.validate_refs({"$ref": "#/components/schemas/Missing"})
        with self.assertRaises(ValueError):
            check.validate_refs({"$ref": "https://example.test/schema"})

    def test_actual_api_matches_documented_routes_and_default_port(self):
        spec = check.verify_api(ROOT)
        self.assertEqual(sum(map(len, spec["paths"].values())), 8)
        self.assertIn("no HTTP authentication", spec["info"]["description"])
        self.assertEqual(spec["components"]["schemas"]["WriteMode"]["default"], "append")

    def test_api_route_changes_are_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("docs/readiness/openapi.json", "Sources/Fluid/Services/LocalAPI/LocalAPIRouter.swift",
                         "Sources/Fluid/Services/LocalAPI/LocalAPIModels.swift",
                         "Sources/Fluid/Services/LocalAPI/HistoryAPIController.swift",
                         "Sources/Fluid/Services/LocalAPI/DictionaryAPIController.swift",
                         "Sources/Fluid/Services/LocalAPI/InferenceAPIController.swift"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text((ROOT / name).read_text())
            path = root / "Sources/Fluid/Services/LocalAPI/LocalAPIRouter.swift"
            path.write_text(path.read_text().replace('"/v1/health"', '"/v1/changed"'))
            with self.assertRaisesRegex(ValueError, "API route drift"):
                check.verify_api(root)

    def test_agents_references_are_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("`tools/missing.py`")
            with self.assertRaisesRegex(ValueError, "missing path"):
                check.verify_agents(root)

    def test_api_dto_changes_are_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [ROOT / "docs/readiness/openapi.json"]
            paths += list((ROOT / "Sources/Fluid/Services/LocalAPI").glob("*.swift"))
            for source in paths:
                destination = root / source.relative_to(ROOT)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(source.read_text())
            controller = root / "Sources/Fluid/Services/LocalAPI/HistoryAPIController.swift"
            controller.write_text(controller.read_text().replace("let characterCount: Int", "let newField: String\n        let characterCount: Int"))
            with self.assertRaisesRegex(ValueError, "API DTO field drift"):
                check.verify_api(root)


class DetectorTests(unittest.TestCase):
    def test_clone_fingerprints_ignore_comments_but_preserve_literal_urls(self):
        code = "\n".join(f'let variable{i} = function({i}, "https://example.test/{i}")' for i in range(20))
        self.assertEqual(list(duplicates.blocks(code)), list(duplicates.blocks(code + "\n// comment")))
        self.assertNotEqual(list(duplicates.blocks(code)), list(duplicates.blocks(code.replace("example.test", "other.test"))))

    def test_repeated_blocks_are_detected_across_production_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "Sources/Fluid"
            source.mkdir(parents=True)
            code = "\n".join(f"let variable{i} = calculate({i}, value: previous{i})" for i in range(20))
            (source / "one.swift").write_text(code)
            self.assertFalse(duplicates.scan(root))
            (source / "two.swift").write_text(code)
            self.assertTrue(duplicates.scan(root))

    def test_bundle_size_reports_largest_files_without_double_counting_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "Example.app"
            app.mkdir()
            (app / "large").write_bytes(b"x" * 50)
            (app / "small").write_bytes(b"x" * 10)
            (app / "link").symlink_to("large")
            report = bundle_size.analyze(app)
            self.assertEqual(report["total_bytes"], 60)
            self.assertEqual(report["largest_files"][0]["path"], "large")

    def test_empty_bundle_and_missing_coverage_are_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "Empty.app"
            app.mkdir()
            with self.assertRaises(ValueError):
                bundle_size.analyze(app)
        with self.assertRaises(ValueError):
            standalone.coverage_report({"data": [{"files": []}]}, {ROOT / "Sources/Fluid/App.swift"})


if __name__ == "__main__":
    unittest.main()
