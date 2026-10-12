# FluidVoice

FluidVoice is a native macOS menu-bar dictation app, built with SwiftUI/AppKit.
The supported app build uses `Fluid.xcodeproj`, scheme `Fluid`, and Swift Package
Manager dependencies. There is no web development server.

## Build and validation

- The user prefers cloud macOS builds because local disk space is limited.
  Keep Xcode on the builder, not this machine. For remote build planning, read
  `docs/readiness/WORKFLOW.md`; ask before launching a cloud
  agent, pushing changes, or triggering a remote workflow.
- Check `xcodebuild -version` before building. Full Xcode is required for app
  builds and XCTest integration on the selected builder. Command Line Tools alone support the
  dependency-free regression subset below, not full app validation.
- Use the public OSS build. The private Fluid Intelligence runtime and its
  private build script are not included in this checkout.
- Preserve the checked-in package pins. Resolve app dependencies with
  `xcodebuild -resolvePackageDependencies -project Fluid.xcodeproj -scheme Fluid`
  after Xcode is available. The root `Package.swift` is not the supported app
  build or XCTest entry point.
- Run the relevant `Tests/run_*_tests.sh` scripts for the changed feature.
  The three standalone suites used by CI are onboarding, release highlights,
  and cloud ASR. These scripts also support Command Line Tools.
- With only Command Line Tools, run `python3 tools/readiness/standalone.py`.
  This runs dependency-free regressions with real coverage and timing.
  Run `sh Tests/run_history_persistence_tests.sh` for persistence or query changes.
  Report full app, integration, and microphone tests as unverified.
- Before finishing any change, run `python3 tools/readiness/check.py` and
  `python3 -m unittest discover -s Tests/Readiness -p 'test_*.py' -v`.
  Test cases use `*Tests.swift`; helpers use `*Fixtures.swift`, `*Doubles.swift`,
  `*Helper.swift` or `*Harness.swift`. Host entry points and Support/Helpers
  directories are separate roles. Python tooling tests use `test_*.py`.
  When changing API routes or DTOs, update `docs/readiness/openapi.json`,
  run `python3 tools/readiness/check.py --generate`, and verify drift checks.
  For dependency, temporary flag or module changes, read
  `docs/readiness/WORKFLOW.md`. For failures and release incidents, use
  `docs/readiness/RUNBOOKS.md`.
- Match CI's SwiftLint version, `0.63.2`. In the prepared local checkout, run:

  ```sh
  .factory/bin/swiftlint-0.63.2/swiftlint lint --strict --config .swiftlint.yml
  ```

  With Command Line Tools, prefix that command with
  `XCODE_DEFAULT_TOOLCHAIN_OVERRIDE=/Library/Developer/CommandLineTools` so
  SourceKitten can find the installed SourceKit framework.

  The downloaded executable is ignored. A new worktree needs its own copy or
  access to a separately installed SwiftLint `0.63.2`. Use SwiftFormat only on
  intended files; do not reformat the whole repository during setup.

After Xcode is available, run the CI-equivalent integration check:

```sh
xcodebuild test \
  -project Fluid.xcodeproj \
  -scheme Fluid \
  -destination 'platform=macOS,arch=arm64' \
  -derivedDataPath DerivedData \
  -skip-testing:FluidDictationIntegrationTests/DictationE2ETests/testDictationEndToEnd_whisperTiny_transcribesFixture \
  CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=NO
```

The Tiny Whisper E2E case is excluded by CI because hosted-runner output is
nondeterministic. Exercise it separately when working on Whisper dictation.

## Running for acceptance

Prefer downloading the `.app` built from the intended commit on a remote macOS
builder, then opening that artifact locally. Running an existing `.app` does
not require local Xcode. Verify the artifact's commit and architecture; a cloud
build does not prove microphone dictation on the user's Mac.

If the user later chooses local builds:

```sh
./build.sh unsigned
open "DerivedData/Build/Products/Debug/FluidVoice Debug.app"
```

Confirm the process exists and the app window opens. Keep the acceptance app
running. Reuse an instance from this checkout; leave unrelated instances alone.
This is a desktop app, so the acceptance entry point is the `.app`, not a URL.

Unsigned rebuilds can require macOS permissions to be granted again. For stable
permissions, `./build.sh` uses an installed Apple Development signing identity.
Select a team via `FLUIDVOICE_DEVELOPMENT_TEAM`, without editing committed team
IDs. Account login, certificate creation, microphone/accessibility permission
approval, and real voice input require the user.

## Feature-specific context

- For visible UI, voice-engine, AI-provider, or onboarding changes, read
  `.devin/skills/verify-fluidvoice/features/README.md` and the relevant feature
  recipe. Use available native GUI tooling; the recipe's `computer` harness
  may not exist in Droid. Keep real-user onboarding and saved credentials intact.
- For localization changes, update the applicable `.xcstrings` catalog and check
  both English and Simplified Chinese. The in-app language switch applies on the
  next launch.
- For provider configuration, keep API keys in macOS Keychain or user-managed
  secrets. Keep credentials, recordings, transcripts, personal signing settings,
  and model downloads out of tracked configuration and readiness artifacts.

## Mission preparation

User-specific Mission models and credentials live in ignored `.factory/` or
user-managed settings. Preserve scrutiny and user-testing validation. Select
available models on each machine; credentials are never repository configuration.
Autonomy inherits user/organization settings; setup does not start a Mission.

The documented readiness command is `/readiness-report`, run inside Droid with
this repository selected. Check CLI command discovery before using older names
such as `/agent-readiness`; a local smoke test is not a Factory readiness report.

`AGENTS.md`, `tools/readiness/` and `docs/readiness/` are shared instructions and
tooling. Ignored `.factory/` setup is local and is not copied into new worktrees.
Check required tool availability before using an isolated worktree.
