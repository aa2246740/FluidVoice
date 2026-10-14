"""Report the largest bundled dependencies/resources and enforce a size budget."""

import argparse
import json
from pathlib import Path

MAX_BYTES = 250 * 1024 * 1024


def analyze(app):
    if not app.is_dir() or app.suffix != ".app":
        raise ValueError(f"Not an application bundle: {app}")
    files = [
        {"path": str(path.relative_to(app)), "bytes": path.stat().st_size}
        for path in app.rglob("*") if path.is_file() and not path.is_symlink()
    ]
    if not files:
        raise ValueError("Empty application bundle")
    files.sort(key=lambda item: item["bytes"], reverse=True)
    return {"total_bytes": sum(item["bytes"] for item in files), "largest_files": files[:30]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    args = parser.parse_args()
    report = analyze(args.app)
    report["budget_bytes"] = MAX_BYTES
    output = Path("quality-artifacts/bundle-size.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["total_bytes"] > MAX_BYTES:
        raise SystemExit("Bundle exceeds 250 MiB; inspect the largest resources/dependencies before increasing the budget")


if __name__ == "__main__":
    main()
