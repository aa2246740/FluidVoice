#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
xcodebuild -version
mkdir -p quality-artifacts
archive="quality-artifacts/FluidVoice-unsigned.zip"
for evidence in "$archive" quality-artifacts/build-metadata.json \
  quality-artifacts/FluidBuild.xcresult quality-artifacts/FluidTests.xcresult; do
  if [ -e "$evidence" ]; then
    printf 'Native evidence already exists: %s. Use a fresh checkout/evidence directory.\n' "$evidence" >&2
    exit 1
  fi
done
metadata() {
  python3 tools/readiness/artifact_metadata.py --archive "$archive" --status "$@"
}
diagnostic_pid=""
stop_diagnostics() {
  if [ -n "$diagnostic_pid" ]; then
    touch quality-artifacts/native-diagnostics.stop
    wait "$diagnostic_pid" || true
    diagnostic_pid=""
  fi
}
interrupted() {
  trap - INT TERM
  stop_diagnostics
  if [ -f "$archive" ]; then metadata interrupted --exit-code "$1" || true; fi
  exit "$1"
}
trap 'interrupted 130' INT
trap 'interrupted 143' TERM
common=(
  -project Fluid.xcodeproj -scheme Fluid
  -destination "platform=macOS,arch=$(uname -m)"
  -derivedDataPath DerivedData
  -clonedSourcePackagesDirPath .build/xcode-packages
  -onlyUsePackageVersionsFromResolvedFile
  -enableCodeCoverage YES
  CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO
  DEBUG_INFORMATION_FORMAT=dwarf
)
python3 tools/readiness/measure.py --name xcode-build-for-testing --output quality-artifacts/timings.json -- \
  xcodebuild build-for-testing "${common[@]}" -resultBundlePath quality-artifacts/FluidBuild.xcresult \
  2>&1 | tee quality-artifacts/xcodebuild.log
app="DerivedData/Build/Products/Debug/FluidVoice Debug.app"
ditto -c -k --sequesterRsrc --keepParent "$app" "$archive"
metadata not_run
bundle_status=0
python3 tools/readiness/bundle_size.py "$app" || bundle_status=$?
python3 tools/readiness/native_diagnostics.py \
  --log quality-artifacts/xcodebuild.log \
  --output quality-artifacts/native-diagnostics \
  --derived-data DerivedData \
  --stop quality-artifacts/native-diagnostics.stop \
  > quality-artifacts/native-diagnostics.log 2>&1 &
diagnostic_pid=$!
set +e
python3 tools/readiness/measure.py --name xcode-test --output quality-artifacts/timings.json -- \
  xcodebuild test-without-building "${common[@]}" \
    -resultBundlePath quality-artifacts/FluidTests.xcresult \
    -test-timeouts-enabled YES \
    -default-test-execution-time-allowance 120 \
    -maximum-test-execution-time-allowance 180 \
    -skip-testing:FluidDictationIntegrationTests/DictationE2ETests/testDictationEndToEnd_whisperTiny_transcribesFixture \
  2>&1 | tee -a quality-artifacts/xcodebuild.log
statuses=("${PIPESTATUS[@]}")
set -e
stop_diagnostics
if [ "${statuses[0]}" -ne 0 ]; then
  metadata failed --exit-code "${statuses[0]}"
  exit "${statuses[0]}"
fi
metadata passed --exit-code 0
if [ "${statuses[1]}" -ne 0 ]; then exit "${statuses[1]}"; fi
xcrun xccov view --report --json quality-artifacts/FluidTests.xcresult > quality-artifacts/app-coverage.json
python3 tools/readiness/check.py
exit "$bundle_status"
