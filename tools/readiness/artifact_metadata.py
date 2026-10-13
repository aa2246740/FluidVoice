"""Record an unsigned artifact's provenance without implying unverified tests passed."""

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def record(archive, status, exit_code, repo=ROOT):
    if status not in {"not_run", "passed", "failed", "interrupted"}:
        raise ValueError("Unknown test status")
    if status == "not_run" and exit_code is not None:
        raise ValueError("Unexecuted tests cannot have an exit code")
    if status == "passed" and exit_code != 0:
        raise ValueError("Passing tests require exit code zero")
    if status in {"failed", "interrupted"} and (exit_code is None or exit_code == 0):
        raise ValueError("Failed/interrupted tests require a nonzero exit code")
    if not archive.is_file() or archive.stat().st_size == 0:
        raise ValueError("Missing or empty unsigned application archive")
    dirty = subprocess.check_output(
        ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"], text=True
    ).strip()
    if dirty:
        raise ValueError("Tracked source or pins changed during native validation")
    return {
        "commit": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
        "architecture": platform.machine(),
        "unsigned": True,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "xcode": subprocess.check_output(["xcodebuild", "-version"], text=True).strip(),
        "working_tree_dirty": False,
        "test_status": status,
        "test_exit_code": exit_code,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--exit-code", type=int)
    parser.add_argument("--output", type=Path, default=ROOT / "quality-artifacts/build-metadata.json")
    args = parser.parse_args()
    metadata = record(args.archive, args.status, args.exit_code)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(metadata, indent=2) + "\n")
    temporary.replace(args.output)


if __name__ == "__main__":
    main()
