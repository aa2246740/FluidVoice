#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
xcodebuild -version
mkdir -p quality-artifacts
python3 tools/readiness/measure.py --name xcode-build-and-test --output quality-artifacts/timings.json -- \
  xcodebuild test \
    -project Fluid.xcodeproj -scheme Fluid \
    -destination "platform=macOS,arch=$(uname -m)" \
    -derivedDataPath DerivedData \
    -clonedSourcePackagesDirPath .build/xcode-packages \
    -onlyUsePackageVersionsFromResolvedFile \
    -resultBundlePath quality-artifacts/FluidTests.xcresult \
    -enableCodeCoverage YES \
    -skip-testing:FluidDictationIntegrationTests/DictationE2ETests/testDictationEndToEnd_whisperTiny_transcribesFixture \
    CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO DEBUG_INFORMATION_FORMAT=dwarf-with-dsym \
  2>&1 | tee quality-artifacts/xcodebuild.log
xcrun xccov view --report --json quality-artifacts/FluidTests.xcresult > quality-artifacts/app-coverage.json
app="DerivedData/Build/Products/Debug/FluidVoice Debug.app"
python3 tools/readiness/bundle_size.py "$app"
ditto -c -k --sequesterRsrc --keepParent "$app" quality-artifacts/FluidVoice-unsigned.zip
python3 - <<'PY'
import hashlib,json,platform,subprocess
from pathlib import Path
archive=Path("quality-artifacts/FluidVoice-unsigned.zip")
metadata={
    "commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
    "architecture":platform.machine(),
    "unsigned":True,
    "sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),
    "xcode":subprocess.check_output(["xcodebuild","-version"],text=True).strip(),
    "working_tree_dirty":bool(subprocess.check_output(["git","status","--porcelain","--untracked-files=no"],text=True).strip()),
}
if metadata["working_tree_dirty"]:
    raise SystemExit("Tracked source or pins changed during native validation; review the diff instead of mislabeling the artifact")
Path("quality-artifacts/build-metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
PY
python3 tools/readiness/check.py
