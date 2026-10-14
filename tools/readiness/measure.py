"""Run a command and retain its wall time and exit status, including failures."""

import argparse
import datetime
import json
import math
import os
import signal
import subprocess
import threading
import time
from pathlib import Path


class CommandInterrupted(Exception):
    def __init__(self, signum):
        self.signum = signum


def save(output, records):
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(records, indent=2) + "\n")
    temporary.replace(output)


def stop_owned_processes(process):
    if process is None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    # The leader can exit while a compiler child ignores SIGTERM.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def run(name, command, output, timeout_seconds=None, log_path=None):
    if not command:
        raise ValueError("A command is required")
    if timeout_seconds is not None and (not math.isfinite(timeout_seconds) or timeout_seconds <= 0):
        raise ValueError("Timeout must be finite and positive")
    stream = None
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # Retain prior evidence; each run must choose a fresh log path.
        stream = log_path.open("x", encoding="utf-8")
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    result = {
        "name": name, "started_at": started, "duration_seconds": None,
        "exit_code": None, "status": "running",
    }
    records = json.loads(output.read_text()) if output.exists() else []
    records.append(result)
    process, previous_handlers = None, {}

    def interrupted(signum, _frame):
        raise CommandInterrupted(signum)

    try:
        save(output, records)
        if threading.current_thread() is threading.main_thread():
            for signum in (signal.SIGINT, signal.SIGTERM):
                previous_handlers[signum] = signal.signal(signum, interrupted)
        process = subprocess.Popen(
            command, start_new_session=True, stdout=stream,
            stderr=subprocess.STDOUT if stream else None,
        )
        if log_path is not None:
            print(f"Running {name}; compiler/command output retained in {log_path}", flush=True)
        status = process.wait(timeout=timeout_seconds)
        result["status"] = "passed" if status == 0 else "failed"
    except subprocess.TimeoutExpired:
        stop_owned_processes(process)
        status, result["status"] = 124, "timed_out"
    except CommandInterrupted as error:
        stop_owned_processes(process)
        status, result["status"] = 128 + error.signum, "interrupted"
    except OSError as error:
        print(f"Cannot start {name}: {error}")
        status, result["status"] = 127, "failed"
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        if stream:
            stream.close()
    result.update({"duration_seconds": round(time.monotonic() - clock, 3), "exit_code": status})
    save(output, records)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write(f"\n| {name} | {result['duration_seconds']} s | exit {status} |\n")
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float)
    parser.add_argument("--log", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    raise SystemExit(run(args.name, command, args.output, args.timeout_seconds, args.log))


if __name__ == "__main__":
    main()
