"""Validate repository contracts and generate actionable quality/debt evidence."""

import datetime
import html
import json
import os
import re
from collections import defaultdict
from pathlib import Path

from debt import inventory as debt_inventory, verify as verify_debt

ROOT = Path(__file__).resolve().parents[2]
EXCLUDED = {".git", ".build", "DerivedData", ".factory", ".venv-readiness", "node_modules", "quality-artifacts"}


def files(root, name):
    for directory, children, names in os.walk(root):
        children[:] = [child for child in children if child not in EXCLUDED]
        if name in names:
            yield Path(directory) / name


def verify_pins(root):
    seen = {}
    graphs = []
    for path in files(root, "Package.resolved"):
        pins = json.loads(path.read_text())
        entries = pins.get("pins", pins.get("object", {}).get("pins", []))
        graphs.append(str(path.relative_to(root)))
        for pin in entries:
            identity = pin.get("identity", pin.get("package", "")).lower()
            state = {key: pin["state"].get(key) for key in ("version", "revision", "branch")}
            if identity in seen and seen[identity][0] != state:
                raise ValueError(f"Dependency drift: {identity} in {seen[identity][1]} and {path.relative_to(root)}")
            seen[identity] = (state, str(path.relative_to(root)))
    if len(graphs) < 2:
        raise ValueError("Expected root and Xcode resolved dependency graphs")
    return {"graphs": graphs, "shared_identity_states": len(seen)}


def verify_test_names(root):
    invalid = []
    for path in (root / "Tests").rglob("*.swift"):
        relative = path.relative_to(root / "Tests")
        # These are explicit helper/host roles, not hidden test-name exceptions.
        if relative.parts[0] in ("Support", "FluidASRBaselineHost") or "Helpers" in relative.parts:
            continue
        if not re.fullmatch(r".+(?:Tests|Fixtures|Doubles|Helper|Harness)\.swift", path.name):
            invalid.append(str(relative))
    for path in (root / "Tests/Readiness").glob("*.py"):
        if not re.fullmatch(r"test_.+\.py", path.name):
            invalid.append(str(path.relative_to(root)))
    if invalid:
        raise ValueError("Invalid test/helper names: " + ", ".join(invalid))


def verify_layers(root, policy):
    from duplicates import TOKENS
    for name in policy["core_files"]:
        text = (root / name).read_text()
        tokens = [
            match.group() for match in TOKENS.finditer(text)
            if not match.group().startswith(("//", "/*", '"'))
        ]
        imports = re.findall(r"\bimport\s+(\w+)", " ".join(tokens))
        if set(imports) & set(policy["forbidden_core_imports"]):
            raise ValueError(f"UI framework imported into domain/core behavior: {name}")
        if set(tokens) & set(policy["forbidden_core_types"]):
            raise ValueError(f"Application orchestration referenced by core behavior: {name}")


def verify_flags(root, policy, today=None):
    from duplicates import TOKENS
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    for flag in policy["temporary_flags"]:
        source = (root / flag["file"]).read_text()
        tokens = [item.group() for item in TOKENS.finditer(source) if not item.group().startswith(("//", "/*"))]
        if tokens.count(json.dumps(flag["key"])) != 1 or tokens.count(flag["symbol"]) < 2:
            raise ValueError(f"Missing or unused temporary flag: {flag['key']}")
        if today >= datetime.date.fromisoformat(flag["review_by"]):
            raise ValueError(f"Temporary flag review overdue: {flag['key']} ({flag['owner']})")
        if not flag["owner"] or not flag["removal_condition"]:
            raise ValueError("Temporary flags require ownership and removal criteria")


def dependency_inventory(root):
    project = (root / "Fluid.xcodeproj/project.pbxproj").read_text()
    products = sorted(set(re.findall(r"productName = ([\w]+);", project)))
    # Ignore native target names; only package product declarations follow package =.
    products = sorted(set(re.findall(r"package = [^;]+;\s*productName = (\w+);", project)))
    usage = defaultdict(list)
    for path in (root / "Sources").rglob("*.swift"):
        for module in re.findall(r"^\s*(?:@preconcurrency\s+)?import\s+(\w+)", path.read_text(), re.M):
            usage[module].append(str(path.relative_to(root)))
    return {
        "products": [{"name": product, "imported_by": usage[product]} for product in products],
        "needs_linkage_review": [product for product in products if not usage[product]],
    }


def validate_refs(spec):
    def walk(value):
        if isinstance(value, dict):
            reference = value.get("$ref")
            if reference:
                if not reference.startswith("#/"):
                    raise ValueError("API schemas must be self-contained")
                target = spec
                for part in reference[2:].split("/"):
                    target = target[part]
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(spec)


def verify_api(root):
    spec = json.loads((root / "docs/readiness/openapi.json").read_text())
    if spec.get("openapi") != "3.1.0":
        raise ValueError("Expected OpenAPI 3.1")
    router = (root / "Sources/Fluid/Services/LocalAPI/LocalAPIRouter.swift").read_text()
    actual = {(method.lower(), path) for method, path in re.findall(r'register\(method: "(\w+)", path: "([^"]+)"', router)}
    documented = {
        (method, path) for path, operations in spec["paths"].items()
        for method in operations if method in ("get", "post", "put", "patch", "delete")
    }
    if documented != actual:
        raise ValueError(f"API route drift: missing={actual - documented}; extra={documented - actual}")
    validate_refs(spec)
    models = (root / "Sources/Fluid/Services/LocalAPI/LocalAPIModels.swift").read_text()
    port = re.search(r"defaultPort: UInt16 = ([\d_]+)", models).group(1).replace("_", "")
    if spec["servers"][0]["url"] != f"http://127.0.0.1:{port}":
        raise ValueError("API default port changed without updating the schema")
    controllers = root / "Sources/Fluid/Services/LocalAPI"
    contracts = [
        ("LocalAPIRouter.swift", "Body", spec["paths"]["/v1/health"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]),
        ("LocalAPIModels.swift", "ErrorBody", spec["components"]["responses"]["Error"]["content"]["application/json"]["schema"]),
        ("HistoryAPIController.swift", "HistoryItem", spec["components"]["schemas"]["HistoryItem"]),
        ("DictionaryAPIController.swift", "ReplacementEntry", spec["components"]["schemas"]["Replacement"]),
        ("DictionaryAPIController.swift", "CustomWordEntry", spec["components"]["schemas"]["CustomWord"]),
        ("InferenceAPIController.swift", "TranscribeResponse", spec["paths"]["/v1/transcribe"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]),
        ("InferenceAPIController.swift", "PostprocessResponse", spec["paths"]["/v1/postprocess"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]),
    ]
    for filename, name, schema in contracts:
        source = (controllers / filename).read_text()
        body = re.search(rf"struct {name}\s*:\s*[^{{]+\{{(.*?)\n\s*\}}", source, re.S)
        if not body:
            raise ValueError(f"Missing API DTO: {name}")
        fields = set(re.findall(r"^\s*let\s+(\w+)\s*:", body.group(1), re.M))
        if fields != set(schema["properties"]):
            raise ValueError(f"API DTO field drift: {name}")
    return spec


def generated_docs(root, spec):
    lines = [
        "# Local API reference", "",
        "Generated by `python3 tools/readiness/check.py --generate`; edit `openapi.json`, not this file.", "",
        "The API is disabled by default. It accepts loopback clients only and has no HTTP authentication.",
        "Any local process can access history or invoke providers after the user enables it.",
        "Keep it disabled on shared machines; never log bodies, dictation text, paths or credentials.", "",
        f"Default endpoint: `{spec['servers'][0]['url']}`.", "",
        "| Method | Path | Operation |", "|---|---|---|",
    ]
    for path, operations in spec["paths"].items():
        for method, operation in operations.items():
            lines.append(f"| {method.upper()} | `{path}` | {operation['summary']} |")
    lines += ["", "Requests are capped at 500 MiB. Responses close the connection. History timestamps use ISO 8601.",
              "See `openapi.json` for request, response, status and nullable-field contracts.", ""]
    return "\n".join(lines)


def verify_agents(root):
    text = (root / "AGENTS.md").read_text()
    for reference in re.findall(r"`((?:tools/|Tests/|docs/)[^`\s]+)`", text):
        if not (root / reference).exists() and not any(root.glob(reference)):
            raise ValueError(f"AGENTS.md references a missing path: {reference}")
    for command in (
        "python3 tools/readiness/check.py", "python3 tools/readiness/standalone.py",
        "sh Tests/run_history_persistence_tests.sh",
    ):
        if command not in text:
            raise ValueError(f"Missing validated AGENTS command: {command}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    policy = json.loads((ROOT / "tools/readiness/policies.json").read_text())
    verify_test_names(ROOT)
    verify_layers(ROOT, policy)
    verify_flags(ROOT, policy)
    debt = verify_debt(ROOT, policy)
    pins = verify_pins(ROOT)
    api = verify_api(ROOT)
    reference = ROOT / "docs/readiness/API.md"
    documentation = generated_docs(ROOT, api)
    if args.generate:
        reference.write_text(documentation)
    if not reference.exists() or reference.read_text() != documentation:
        raise SystemExit("Generated API documentation is stale; run check.py --generate")
    verify_agents(ROOT)
    project = (ROOT / "Fluid.xcodeproj/project.pbxproj").read_text()
    if project.count("SWIFT_STRICT_CONCURRENCY = complete;") < 2:
        raise SystemExit("Strict concurrency checking is required for Debug and Release")
    report = {
        "dependency_pins": pins, "dependencies": dependency_inventory(ROOT),
        "technical_debt": debt, "temporary_flags": policy["temporary_flags"],
        "validated_api_operations": sum(len(operations) for operations in api["paths"].values()),
        "test_naming": "passed", "core_boundaries": "passed", "agents_references": "passed",
        "technical_debt_gate": "passed",
    }
    output = ROOT / "quality-artifacts"
    output.mkdir(exist_ok=True)
    (output / "contracts.json").write_text(json.dumps(report, indent=2) + "\n")
    rows = [
        ("Technical debt markers", len(report["technical_debt"])),
        ("Dependency products needing linkage review", ", ".join(report["dependencies"]["needs_linkage_review"]) or "none"),
        ("Validated API operations", report["validated_api_operations"]),
    ]
    for name in ("core-coverage.json", "bundle-size.json", "standalone-timings.json", "timings.json", "duplication.json"):
        path = output / name
        rows.append((name, json.dumps(json.loads(path.read_text())) if path.exists() else "Not measured in this environment"))
    body = "<h1>FluidVoice quality evidence</h1><p>Missing measurements are not passing results.</p><table>"
    body += "".join(f"<tr><th>{html.escape(str(key))}</th><td><pre>{html.escape(str(value))}</pre></td></tr>" for key, value in rows)
    body += "</table>"
    (output / "index.html").write_text("<!doctype html><meta charset=utf-8><title>FluidVoice quality</title>" + body)
    print(f"Repository contracts passed; debt markers={len(report['technical_debt'])}; API operations={report['validated_api_operations']}")


if __name__ == "__main__":
    main()
