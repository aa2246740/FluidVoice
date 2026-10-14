#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
test_dir="$(mktemp -d "${TMPDIR:-/tmp}/fluidvoice-clamshell-callback.XXXXXX")"
trap 'rm -rf "$test_dir"' EXIT
python3 - "$test_dir/ClamshellCallbackIsolationTests.swift" <<'PY'
import re
import sys
from pathlib import Path

source = Path("Sources/Fluid/Services/AudioDeviceService.swift").read_text()
callback = re.search(
    r"(?m)^private(?: nonisolated)? func clamshellStateInterestCallback\([\s\S]*?\n\}",
    source,
)
if callback is None:
    raise SystemExit("Production clamshell callback not found; update the harness for its new boundary")
fixture = Path("Tests/ClamshellCallbackIsolationTests.swift").read_text()
Path(sys.argv[1]).write_text(fixture + "\n" + callback.group() + "\n")
PY
xcrun swiftc -swift-version 5 -default-isolation MainActor \
    -strict-concurrency=complete -warnings-as-errors \
    -target "$(uname -m)-apple-macosx15.0" -parse-as-library \
    "$test_dir/ClamshellCallbackIsolationTests.swift" -o "$test_dir/tests"
"$test_dir/tests"
