# Incident response

Owner: `@aa2246740`. Treat recordings, transcripts, dictionary words, provider
credentials and window titles as private. Never upload raw Library directories.

## Build or release failure

1. Stop publication; leave the last known-good release available.
2. Identify the failing run and exact commit in GitHub Actions. Download only
   relevant quality/native artifacts. Inspect `timings.json`, `xcodebuild.log`,
   `FluidTests.xcresult`, coverage and bundle-size reports.
3. Confirm Xcode 26+, runner architecture, package pins and unsigned/public build.
   Cache corruption: rerun with that run's build cache removed, not new dependency
   versions. Record cache key and error first.
4. Reproduce the narrow failing suite. Fix and request one bounded native run.
   Do not repeatedly dispatch paid agents without an agreed attempt/budget limit.
5. Release only after the quality gate and native checks pass. For unsigned previews,
   verify architecture, commit and SHA-256 before local opening.
6. If a published preview regresses, mark it as a prerelease and direct users to
   the last verified artifact. Preserve evidence and open a labeled incident issue.

## Dictation or meeting failure

1. Stop recording from the app; do not delete meeting/history data or kill an
   unrelated audio process. Record app/macOS/engine/model versions and whether
   audio is recoverable, without recording actual speech in the issue.
2. Inspect local redacted `Fluid.log` and `Fluid.crash.log` for pipeline/session IDs, failure code and stack.
   For a crash, pair the macOS `.ips` report with matching build/dSYM information.
   Obtain user permission and review redaction before sharing any report.
3. Check microphone/accessibility permission, selected input/output device,
   available memory/disk and model residency. User approves permission prompts.
4. An AEC3-specific regression may use `FLUIDVOICE_DISABLE_AEC3` for a bounded
   reproduction; record the flag and restore the normal setting afterward.
5. Run the feature's verification recipe. Real microphone/hardware acceptance is
   separate from hosted-runner or fixture results.
6. Track the incident with `type:bug`, a priority and relevant area. Close only
   after the affected scenario succeeds, not just after a code change lands.

## Credential or private-data exposure

1. Stop sharing affected logs/artifacts and stop publication of the affected build.
   Do not paste the secret into chat, source, an issue or a terminal command.
2. Have the credential owner revoke/rotate it in the provider's console.
3. Inspect redaction tests and the leaking call site with synthetic values.
   Remove raw user-content logging rather than expanding permissive patterns.
4. Fix the relevant sink and add a regression before rebuilding.
5. Remote artifact/issue removal and history rewriting require explicit owner
   approval. Record what was removed, who was notified and residual exposure.

## Where to inspect release impact

Repository release/build evidence lives in this repository's GitHub Actions runs
and Releases. Compare commit, runner architecture, bundle bytes, core coverage,
test durations and incident issue counts before/after a preview.
There is currently no verified production crash/latency dashboard for this fork.
Do not equate artifact metrics with real-time deployed-user health.
