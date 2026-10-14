"""Capture owned native test process stacks before XCTest's timeout terminates them."""

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

CASE = re.compile(r"Test Case '(.+?)' (started|passed|failed)(?:\.|\s)")


class TestProgress:
    def __init__(self, threshold=90):
        self.threshold = threshold
        self.active = {}
        self.sequence = 0

    def feed(self, line, now):
        match = CASE.search(line)
        if not match:
            return
        name, state = match.groups()
        if state == "started":
            self.sequence += 1
            self.active[name] = {"started": now, "sequence": self.sequence, "captured": False}
        else:
            self.active.pop(name, None)

    def due(self, now):
        result = []
        for name, state in self.active.items():
            if not state["captured"] and now - state["started"] >= self.threshold:
                state["captured"] = True
                result.append((name, state["sequence"], round(now - state["started"], 3)))
        return result


def owned_processes(text, derived_data):
    prefix = str(derived_data.resolve()) + "/"
    result = []
    for line in text.splitlines():
        fields = line.strip().split(maxsplit=1)
        if len(fields) != 2 or not fields[0].isdigit():
            continue
        pid, executable = fields
        canonical = str(Path(executable).resolve())
        if canonical.startswith(prefix) and ".app/Contents/MacOS/" in executable:
            result.append((int(pid), Path(executable).name))
    return result[:4]


def capture(name, sequence, elapsed, output, derived_data):
    output.mkdir(parents=True, exist_ok=True)
    report = {"test": name, "elapsed_seconds": elapsed, "processes": []}
    try:
        processes = subprocess.check_output(
            ["/bin/ps", "-axo", "pid=,comm="], text=True, timeout=10
        )
        for pid, executable in owned_processes(processes, derived_data):
            stack = output / f"test-{sequence}-pid-{pid}.sample.txt"
            try:
                result = subprocess.run(
                    ["/usr/bin/sample", str(pid), "3", "1", "-file", str(stack)],
                    capture_output=True, text=True, timeout=15,
                )
                report["processes"].append({
                    "pid": pid, "executable": executable, "exit_code": result.returncode,
                    "stack_file": stack.name if stack.exists() else None,
                })
            except (OSError, subprocess.TimeoutExpired) as error:
                report["processes"].append({"pid": pid, "error": type(error).__name__})
    except (OSError, subprocess.SubprocessError) as error:
        report["error"] = type(error).__name__
    (output / f"test-{sequence}.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Captured native timeout diagnostic for test {sequence}: {name}", flush=True)


def watch(log, output, derived_data, stop, threshold):
    progress = TestProgress(threshold)
    with log.open(encoding="utf-8", errors="replace") as stream:
        # The watcher starts before test-without-building, after the build log.
        stream.seek(0, 2)
        while not stop.exists():
            for line in stream:
                progress.feed(line, time.monotonic())
            for name, sequence, elapsed in progress.due(time.monotonic()):
                capture(name, sequence, elapsed, output, derived_data)
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--derived-data", type=Path, required=True)
    parser.add_argument("--stop", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=90)
    args = parser.parse_args()
    if args.threshold <= 0:
        parser.error("The diagnostic threshold must be positive")
    watch(args.log, args.output, args.derived_data, args.stop, args.threshold)


if __name__ == "__main__":
    main()
