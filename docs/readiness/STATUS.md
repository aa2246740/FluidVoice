# Agent Readiness remediation evidence

Baseline: `main@9f2ab4a9`, official report 53.85%, Level 3.
Official baseline date: 2026-10-12. Tracker updated: 2026-10-14.
This is an implementation tracker, **not a new official score**.
The latest native validation revision is `ef99f1e2`; this follow-up remains local
and unpublished. Configuration does not prove remote operation.

## 2026-10-14 local follow-up

- All five existing debt comments are registered against the real fork work item
  [#7](https://github.com/aa2246740/FluidVoice/issues/7), with owner, resolution and
  a 2026-11-13 review deadline. CI now rejects unregistered or copied debt,
  stale registrations and overdue/missing ownership metadata. The comments and
  underlying product behavior are unchanged; this is tracking, not debt elimination.
- The scanner distinguishes comments from normal/raw/multiline string literals
  and handles nested block comments. Regressions reproduced the previous missing
  block-comment debt and false literal finding before the repair.
- The latest existing [CodeQL run](https://github.com/aa2246740/FluidVoice/actions/runs/38353722610)
  is confirmed cancelled during compiler tracing after approximately 25 minutes;
  analysis never ran. Its earlier cache post-step was also skipped on cancellation.
  The revised workflow saves resolved package downloads before tracing, partitions
  them by toolchain/pins, retains a cold product build, and gives resolution and
  tracing independent 300/1,800-second deadlines. Analysis has a separate ten-minute
  allowance within a bounded 60-minute standard-runner job.
- The real process runner records `running`, terminal failure/timeout/interruption
  and durations, retains partial logs, and terminates only its own process group,
  including compiler descendants that ignore SIGTERM. Existing logs are preserved,
  not overwritten. Native full-app compilation/CodeQL extraction under this new
  workflow remains unverified until an approved cloud run.
- 54 Python regression tests, repository contracts, no-new-duplication checks and
  workflow YAML/shell syntax pass locally. Seven real Swift programs pass with
  89.61% critical production coverage. One existing onboarding fixture emits the
  Swift 6.4 `WeakMutability` warning; no warning-free full-app claim is made.
- No branch publication, CI dispatch, release, merge or paid resource was started
  for this follow-up. Official readiness has not been rerun.

## Authorized GitHub follow-up

- Issues enabled; two real, assigned work items created:
  [native acceptance #6](https://github.com/aa2246740/FluidVoice/issues/6) and
  [dependency/duplication debt #7](https://github.com/aa2246740/FluidVoice/issues/7).
- 17 priority/type/area labels created.
- Active `main-pull-request-guard` ruleset requires a PR, resolved review threads
  and protects against force pushes/deletion, with no bypass actors. The approved
  personal-repository policy requires zero human approvals. A required
  `Quality gate` check is deferred until that workflow is active on `main`.
- Dependency graph, Dependabot alerts and security updates enabled using the
  existing browser login; CLI authentication scopes were not expanded.
- First validation-branch [App CI run](https://github.com/aa2246740/FluidVoice/actions/runs/38286323674)
  tested `0fb6b337`. Repository checks, strict lint and every standalone/persistence/
  privacy regression passed; cloud critical-source coverage was 89.06%.
  Xcode 26.6 compilation failed at the clamshell C callback/actor boundary after
  147.222 seconds; XCTest was cancelled and no App was produced.
- A production-callback/real-IOKit-ABI regression reproduces that error with the
  app's actor settings. The callback fix keeps strict checking and synchronously
  enters MainActor because IOKit is explicitly configured to deliver on the main
  queue.
- The second authorized [App CI run](https://github.com/aa2246740/FluidVoice/actions/runs/38330797552)
  tested `c11c890e`. Repository checks, strict lint and all standalone/persistence/
  privacy regressions passed, including the real callback regression. Critical-source
  coverage remained 89.06%. The App compiled, linked and launched on the runner.
  Three meeting-scope XCTest cases passed; then
  `testMeetingTranscriptionEntryPointsRunWithinScopeAndUnclaimedLegacyPath` started
  at 01:17:47 UTC and never completed before the 25-minute job cap cancelled the run.
  The quality gate failed. The exact hang cause is not proven.
- No App archive was produced by that run because the old combined build/test
  script packaged only after successful tests. A local script revision now preserves
  archives before tests, records explicit test state and applies bounded per-test
  timeouts without adding exclusions. Tooling tests validate metadata,
  build/test/log failures, interruption and stale evidence. A watchdog samples
  only this checkout's test-app processes after a case runs for 90 seconds, before
  the default 120-second timeout, and retains stack files and diagnostic status.
  Temporary tagged test-boundary logs were used to narrow the meeting ASR wait.
- On 2026-10-13, the user authorized publication of this follow-up, a PR to `main`
  without merging, a third standard/free macOS CI round and evidence-led follow-up
  rounds if needed. Paid runners/services, releases, deletion and merges remain
  prohibited. Omarchy was read-only at that point; a later separate authorization
  permitted user-directory toolchain installation, not a FluidVoice upload/build.
  Full XCTest, whole-app coverage and local App acceptance require actual results.
- Follow-up commit `c23b9afe` is published as [PR #8](https://github.com/aa2246740/FluidVoice/pull/8).
  The third [CI run](https://github.com/aa2246740/FluidVoice/actions/runs/38348120086)
  passed quality/lint/regressions and built for testing successfully. Its App
  archive was retained with `not_run` status, but the 250 MiB budget blocked XCTest:
  278,932,018 bytes included a 42,693,784-byte embedded test dSYM. No ASR hang
  diagnostic was produced because tests had not started.
- The next diagnostic revision uses Debug DWARF without generating the embedded
  test dSYM and runs XCTest even when the size report fails; the original 250 MiB
  budget still fails the final gate. A red-to-green tooling regression verifies
  this separation. No tests are removed, no data is deleted and no budget is raised.
- Revision `a8605300` passed the fourth [standard macOS CI run](https://github.com/aa2246740/FluidVoice/actions/runs/38350202351).
  XCTest recorded 1,811 tests, 29 conditionally skipped and zero failures; the
  existing Tiny Whisper exclusion is unchanged. The previously hanging meeting
  entry-point case passed in 0.019 seconds, and all 12 meeting-scope cases passed.
  All seven tagged wait boundaries completed. The App measured 236,237,281 bytes,
  below the unchanged 250 MiB budget. Build, tests and Quality gate passed.
- This does not establish the original ASR hang's root cause: it did not recur,
  no production ASR logic was changed and no hang stack was captured. The same-revision
  fifth [CI run](https://github.com/aa2246740/FluidVoice/actions/runs/38351936205)
  also passed: 1,811 tests, 29 conditional skips and zero failures. The meeting
  entry-point case passed in 0.053 seconds; bundle size and critical coverage were
  unchanged. Temporary test markers are removed for a final confirmation without
  their possible timing effects; the permanent watchdog remains.
- Marker-free revision `ef99f1e2` passed the sixth [CI run](https://github.com/aa2246740/FluidVoice/actions/runs/38353722599):
  1,811 tests, 29 conditional skips and zero failures in 186.081 seconds. The
  original meeting case passed in 0.042 seconds; its body is unchanged from
  `c11c890e`. The bundle was 236,237,041 bytes and critical coverage 89.06%.
  This is three consecutive native-suite greens, not proof of the hang's cause.
- PR archive builds passed for both `c23b9afe` and `a8605300`, producing separate
  ad-hoc-signed acceptance artifacts. Large native-artifact downloads to this Mac
  have stalled, while logs/small reports download successfully. Local App launch,
  microphone and accessibility acceptance therefore remain unverified.
- Third-party production tracking is optional for Missions. No paid service or
  runtime data upload is enabled; production-only signals remain unverified.

## Local evidence

- 54 Python tooling regression tests.
- Seven instrumented Swift regression programs, critical production line coverage
  89.61% with an enforced 75% floor. Whole-app coverage reports were generated by
  passing cloud validation; their percentages have not yet been retrieved locally.
- History persistence tests: 8,400 rows, migration/rollback/recovery/statistics and
  one SELECT per history read.
- Real log sinks tested in a temporary baseline directory with Swift 6 complete
  concurrency and warnings-as-errors. Secrets/content/paths are scrubbed; errors
  retain bounded breadcrumbs and caller stack frames. Existing support log and
  directory permissions are repaired to 0600/0700. Signal byte storage is
  initialized before registering handlers. The logger also type-checks with the
  app's Swift 5/MainActor/macOS 15 settings and warnings-as-errors.
- Strict SwiftLint 0.63.2 passed after fixing eight existing violations.
- Root pins aligned to the supported Xcode graph and successfully re-resolved.
  Xcode app pins and personal development-team IDs remain unchanged.
- Repository contracts validate test names, core boundaries, temporary flags,
  API operations/DTO fields, generated docs, AGENTS references and version drift.
- 248 legacy duplicate windows inventoried; new/expanded duplication is rejected.
  Existing duplication is not falsely described as eliminated.
- Workflow YAML and shell syntax checked. Native compilation, runner launch and the
  CI-selected XCTest suite now have a successful fourth-run result and durations;
  test omissions and unverified hardware acceptance remain explicit.
  All three existing CodeQL runs were cancelled; the latest trace was cancelled and
  `ef99f1e2` analysis step was skipped. No successful security assessment is claimed.
  Container boot and preview release remain unverified.
- A temporary no-network probe extracted the actual `TranscriptionExecutor`,
  used a MainActor-bound fake provider, drained it and reused it under the app's
  compiler settings. It passed within a 10-second limit. This does not reproduce
  the complete ASRService scope hang; no speculative ASR logic change was made.
- Separately authorized Omarchy setup registered an official anonymously downloaded
  CLT 27 macOS SDK. An independent SwiftPM package cross-compiled and ad-hoc signed,
  with native Mac strict signature verification and tamper rejection. SwiftUI/
  AppKit/IOKit, explicit macro expansion and resource fixtures passed. SwiftBuild,
  full FluidVoice compilation and macOS runtime/microphone acceptance were not
  performed; the experimental linker warning remains. This is not app CI evidence.

## All 36 signals

| Signal | Implemented change | Remaining evidence or authorization |
|---|---|---|
| strict_typing | Complete concurrency checks in app/baseline Debug and Release; logger tests compile as Swift 6 with warnings-as-errors; real IOKit ABI/actor regression | App compiled in the second run; existing Swift 5 concurrency warnings remain, not a whole-app Swift 6 warning-free claim |
| duplicate_code_detection | Actual Swift block detector, legacy inventory and new-clone gate | Both cloud checks passed; legacy refactoring remains debt |
| code_modularization | Enforced core imports/singleton boundaries | Local contract tests pass |
| tech_debt_tracking | Actual-comment inventory and owner/issue/resolution/review-date contract; new/copied/unregistered or stale debt fails CI | All five existing markers link to assigned fork issue #7; resolution and periodic review remain debt |
| n_plus_one_detection | Production SQLite read-statement counter plus 8,400-row query-budget regression | Local tests pass |
| automated_pr_review | Privileged-safe consumer generates reviews from real lint findings, with stale-head checks | Enable workflow on default branch; observe real review content |
| fast_ci_feedback | PR-API-independent diff, parallel quick checks and stable required gate | Fourth PR validation passed; native build/test timing is retained, not inferred from earlier quick failures |
| build_performance_tracking | Toolchain/pin-partitioned package and incremental caches; wall-time records; separate build/test timing | Fourth and fifth native validations passed with separate timings; sustained cache performance needs more history |
| deployment_frequency | Safe preview release path prepared | Real approved shipping history; cannot manufacture multiple weekly releases |
| release_notes_automation | GitHub generated release notes in draft preview pipeline | Execute an approved preview release |
| heavy_dependency_detection | 250 MiB app budget and largest-resource/dependency report | Real instrumented Debug bundle measured at 236,237,281 bytes; release/archive size remains a separate measurement |
| unused_dependencies_detection | Package product/import inventory identifies AppUpdater for linkage review | Verify transitive PromiseKit usage before any removal |
| version_drift_detection | All checked-in resolved graphs compared; six shared pin forks repaired without changing app pins | Local resolver and checks pass; out-of-tree evaluation SDK is separately user-managed |
| release_automation | Tested-source build, provenance/hash, draft unsigned prerelease pipeline | Activate and run workflow; no stable signing/notarization claimed |
| dead_feature_flag_detection | Source-use checks, ownership, review deadline, removal condition for AEC3 escape hatch | Local lifecycle checks pass; real-meeting stability controls removal |
| test_performance_tracking | Per-program/native timers; retained xcresult/log/coverage artifacts; bounded per-test execution | Passing native suite timings: 180.183 / 195.362 / 186.081 seconds in rounds four–six; original hang cause remains unproven |
| test_coverage_thresholds | Actual standalone production coverage enforced at 75% | 89.61% locally, 89.06% on Xcode runner; no whole-app threshold claim |
| test_naming_conventions | Explicit Swift/Python test/helper roles, docs and rejecting checks | Local tests pass |
| automated_doc_generation | API reference generation plus stale-output gate | Local generation and checks pass |
| api_schema_docs | OpenAPI 3.1 for all eight methods with requests/responses/errors/privacy, route/DTO drift checks | Local checks pass; live API behavior still needs app acceptance |
| agents_md_validation | References and required commands checked; documented commands executed in validation | Local checks pass |
| devcontainer | Usable Python repository-automation container configuration | Boot not tested; cannot substitute for macOS/Xcode |
| code_quality_metrics | Persisted coverage, debt, duplication, dependency, timing and bundle evidence; offline HTML view | Native size/timings measured; whole-app coverage file generated but percentage not yet retrieved |
| error_tracking_contextualized | Real on-device redacted stacks, breadcrumbs, per-run context and stable crash sink | No production tracking service enabled; requires privacy/service approval |
| alerting_configured | Default-branch CI/release failure alerts create actionable assigned issues; Issues now enabled | Activate default-branch workflow; not production-runtime paging |
| runbooks_documented | Concrete build/release/audio/credential incident procedures and links | Locally documented |
| deployment_observability | Release/build provenance and artifact metric inspection documented | No verified real-time deployed-user dashboard |
| branch_protection | Active main PR/force-push/deletion ruleset, no bypass actors, zero required human approvals | Required quality-gate check awaits default-branch activation |
| codeowners | Valid maintainer ownership and path routing, published on the validation branch | Default-branch activation awaits an authorized merge |
| automated_security_review | Swift CodeQL cold tracing, pre-trace package cache, independent deadlines and retained failure logs/provenance plus SARIF when produced | Three existing tracing runs cancelled; revised workflow requires a real successful cloud scan, not merely passing tooling tests |
| dependency_update_automation | Weekly Swift/Actions Dependabot configuration with cooldown and labeled groups; repository security updates enabled | Activate version-update configuration on default branch and observe real PRs |
| log_scrubbing | Real sinks, broad auth/cookie/content/path redaction, private file permissions and regressions | Local sink and privacy tests pass |
| min_release_age | Explicit seven-day merge policy and seven-day bot cooldown | Apply policy to actual updates |
| issue_labeling_system | 17 priority/type/area GitHub labels created, matching bot configuration | Labels applied to the two actual work items |
| backlog_health | Issues enabled; acceptance #6 and dependency/debt #7 assigned and prioritized | Maintain these real work items as validation progresses |
| error_to_insight_pipeline | CI incident-to-issue automation prepared | Production errors are not uploaded; production tracking/issue integration requires service and consent |
