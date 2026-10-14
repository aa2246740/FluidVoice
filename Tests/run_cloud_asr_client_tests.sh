#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
xcrun --find swiftc >/dev/null
task_test_dir=$(mktemp -d /tmp/fluidvoice-cloud-asr.XXXXXX)
trap 'rm -rf "$task_test_dir"' EXIT
xcrun swiftc -parse-as-library Sources/Fluid/String+Localization.swift Sources/Fluid/Services/CloudASR/CloudASRClient.swift Tests/CloudASRClientTests.swift -o "$task_test_dir/tests"
"$task_test_dir/tests"
