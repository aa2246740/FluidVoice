#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
xcrun --find swiftc >/dev/null
task_test_dir=$(mktemp -d /tmp/fluidvoice-highlights.XXXXXX)
trap 'rm -rf "$task_test_dir"' EXIT
xcrun swiftc -parse-as-library Sources/Fluid/UI/ReleaseHighlightsPolicy.swift Sources/Fluid/UI/ReleaseHighlightsContent.swift Tests/ReleaseHighlightsPolicyTests.swift -o "$task_test_dir/tests"
"$task_test_dir/tests"
