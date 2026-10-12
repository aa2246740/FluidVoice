"""Run a command and retain its wall time and exit status, including failures."""

import argparse
import datetime
import json
import os
import subprocess
import time
from pathlib import Path


def run(name, command, output):
    if not command:
        raise ValueError("A command is required")
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    try:
        status = subprocess.run(command, check=False).returncode
    except OSError as error:
        print(f"Cannot start {name}: {error}")
        status = 127
    result = {
        "name": name, "started_at": started,
        "duration_seconds": round(time.monotonic() - clock, 3),
        "exit_code": status,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    records = json.loads(output.read_text()) if output.exists() else []
    records.append(result)
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(records, indent=2) + "\n")
    temporary.replace(output)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write(f"\n| {name} | {result['duration_seconds']} s | exit {status} |\n")
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    raise SystemExit(run(args.name, command, args.output))


if __name__ == "__main__":
    main()
