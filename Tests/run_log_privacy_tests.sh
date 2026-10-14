#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
test_dir="$(mktemp -d "${TMPDIR:-/tmp}/fluidvoice-log-privacy.XXXXXX")"
trap 'rm -rf "$test_dir"' EXIT
xcrun swiftc -swift-version 6 -strict-concurrency=complete -warnings-as-errors \
    -D FLUID_ASR_BASELINE -parse-as-library \
    Sources/Fluid/Services/LogSanitizer.swift \
    Sources/Fluid/Services/FileLogger.swift \
    Sources/Fluid/Services/DebugLogger.swift \
    Tests/LogSinkIntegrationTests.swift -o "$test_dir/tests"
"$test_dir/tests"
