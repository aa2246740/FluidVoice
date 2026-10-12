"""Detect native build changes without privileged pull-request API access."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD_FILES = {
    "Package.swift", "Package.resolved", "Info.plist", "Fluid.entitlements",
    "build.sh", ".swiftlint.yml", ".github/workflows/build.yml",
    "tools/readiness/native_ci.sh", "tools/readiness/standalone.py",
}


def relevant(path):
    return (
        path in BUILD_FILES
        or path.startswith(("Sources/", "Vendor/", "Fluid.xcodeproj/"))
        or (path.startswith("Tests/") and not path.startswith("Tests/Readiness/"))
    )


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def changed_files(repo, event, payload):
    if event == "pull_request":
        # actions/checkout checks out the event's synthetic merge commit.
        # Its first parent is the base; this includes the entire PR, not just
        # the last commit, and needs no pull-requests:read permission.
        return git(repo, "diff", "--name-only", "-z", "HEAD^1", "HEAD")
    before = payload.get("before", "")
    if event == "push" and re.fullmatch(r"[0-9a-f]{40}", before) and set(before) != {"0"}:
        try:
            git(repo, "cat-file", "-e", before + "^{commit}")
        except subprocess.CalledProcessError:
            # Multi-commit pushes can exceed checkout's shallow history.
            subprocess.run(
                ["git", "-C", str(repo), "fetch", "--no-tags", "--depth=1", "origin", before],
                check=True,
            )
        return git(repo, "diff", "--name-only", "-z", before, "HEAD")
    return git(repo, "ls-files", "-z")


def detect(repo, event, payload):
    files = [
        item.decode("utf-8", errors="surrogateescape")
        for item in changed_files(repo, event, payload).split(b"\0") if item
    ]
    return {"relevant": any(map(relevant, files)), "files": files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--event", default=os.environ.get("GITHUB_EVENT_NAME", "local"))
    parser.add_argument("--payload", type=Path)
    args = parser.parse_args()
    payload_path = args.payload or (
        Path(os.environ["GITHUB_EVENT_PATH"]) if os.environ.get("GITHUB_EVENT_PATH") else None
    )
    payload = json.loads(payload_path.read_text()) if payload_path else {}
    result = detect(args.repo, args.event, payload)
    print(json.dumps(result, ensure_ascii=True))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"relevant={str(result['relevant']).lower()}\n")


if __name__ == "__main__":
    main()
