# Development and quality workflow

## Validation environments

- Command Line Tools: `python3 tools/readiness/standalone.py` and
  `sh Tests/run_history_persistence_tests.sh`. These execute production behavior
  and isolated fixtures; they do not build the app or prove microphone operation.
- Repository tooling: `python3 tools/readiness/check.py`,
  `python3 tools/readiness/duplicates.py`, and
  `python3 -m unittest discover -s Tests/Readiness -p 'test_*.py' -v`.
- `.devcontainer/devcontainer.json` supplies Python tooling for repository
  automation. It does not provide the macOS runtime, Xcode or audio acceptance.
  Do not download a local container image on a space-constrained Mac without asking.
- Experimental Linux macOS cross-compilation is separate from native acceptance;
  see `LINUX-BUILD-RESEARCH.md`. The authorized Omarchy SDK/toolchain passed an
  independent SwiftPM arm64 macOS fixture, framework imports, explicit macro
  expansion, resources and native Mac signature checks. It has not built FluidVoice,
  validated SwiftBuild or run the macOS app. Uploading/adapting the product requires
  separate approval. The supported app build remains the Xcode project below.
- Native validation: use a remote macOS machine with Xcode 26 or newer.
  `bash tools/readiness/native_ci.sh` retains XCTest results, full-app coverage,
  timing, dependency size analysis and an unsigned app with commit/architecture/hash.
  Source must be available on the builder; ask before publishing a branch,
  uploading a patch, starting a paid agent or triggering a workflow.
- This user's Devin browser exposes Hosted macOS. Only environment inspection
  was authorized during setup, not an ongoing or unlimited build budget.

## CI contracts

The workflow uses a git merge-parent diff for PRs and before-to-HEAD diff for
pushes. It handles multi-commit pushes and NUL-delimited filenames without
requiring PR API permissions. Documentation changes still run repository checks.
Native changes require lint, repository checks and native test success through
the stable `Quality gate` check. A failed or unexpectedly skipped required job
must not become a passing gate.

Timing and XCTest artifacts survive failures. Incremental build caches are
partitioned by OS, architecture, exact Xcode version and resolved package hashes.
`quality-artifacts/index.html` is an offline quality evidence view, not a hosted
production dashboard or app acceptance URL. App coverage is reported separately.
The enforceable 75% line threshold covers the named standalone production sources;
it is not a claim of 75% coverage across the whole application.
Unsigned app bundles have a 250 MiB budget and a largest-file report.
Native validation builds for testing first, then saves the unsigned archive and
commit/hash metadata before running XCTest without rebuilding. `test_status` is
explicitly `not_run`, `passed`, `failed` or `interrupted`; an archive alone does not
prove acceptance. Failed/interrupted tests still fail CI and retain the archive.
Each test has a 120-second default allowance and 180-second maximum; the existing
Tiny Whisper exclusion is unchanged. Build and test timings are separate.
Use a fresh checkout/evidence directory for a new run; existing native artifacts
are rejected, not deleted or reused. This control flow passed three consecutive
native runs, including marker-free `ef99f1e2`; each new cloud run still needs approval.
While native tests run, a watchdog samples only application executables under
the current checkout's DerivedData path after a case lasts 90 seconds. The
`native-diagnostics/` stack samples and JSON status precede XCTest termination;
sampling failures are retained rather than claimed as successful diagnostics.
Temporary test markers distinguished scoped transcription, scope drain and the
unclaimed legacy path in two passing runs, then were removed. The original test
passed again without them. Its original hang's root cause remains unproven.
Debug validation uses DWARF without an embedded test dSYM. A size-budget failure
still allows XCTest and stack diagnostics to run, then fails the final native
gate; the 250 MiB budget is unchanged.

## Security scan evidence

The CodeQL workflow preserves a cold product build so compiler tracing sees the
actual application sources. Only resolved package downloads are cached, keyed by
OS, architecture, Xcode version and pins; they are saved before tracing so a later
cancellation cannot lose the cache. No DerivedData build products are reused.

Resolution is bounded at five minutes, tracing at thirty, analysis at ten, with
separate step allowances and a sixty-minute job cap. `measure.py` records pending
state before execution, final status and durations, and retains partial compiler
logs on timeout/interruption. Cleanup targets only the command's own process group.
Choose a fresh `--log` path; existing logs are rejected rather than overwritten.

Inspect `security-assessment` artifacts for `provenance.txt`, `toolchain.log`,
`timings.json`, package-resolution/compiler logs and SARIF when analysis produced
it. `running`/null exit after a hard cancellation is incomplete evidence, not a pass.
A build timing record does not prove CodeQL analysis. Use the security-scan branch
in `RUNBOOKS.md` for failures; the revised workflow awaits an approved real scan.

## Dependency governance

Wait **at least 7 days after a dependency release before merging its version bump**.
Dependabot runs weekly with a 7-day cooldown. An urgent security exception requires
a documented maintainer decision and targeted regression evidence.
Never silently rewrite checked-in pins during setup.

The drift checker compares shared identities and resolved states across every
checked-in build graph. The supported Xcode app lock is authoritative. When
repairing drift or updating dependencies, review `python3 tools/readiness/sync_pins.py`
then explicitly use `--write` to align shared root pins; root-only pins remain intact.
Re-resolve the root graph and rerun checks. This does not upgrade the app.
Package product/import inventories highlight potential
unused dependencies. Review transitive linkage (including AppUpdater/PromiseKit)
before removing a product; a missing direct import is a finding, not conclusive
proof that removal is safe. Build and test the affected target after removal.

## Core boundaries and technical debt

The explicitly listed foundation/core behavior files in `policies.json` may not
import SwiftUI/AppKit or reference app orchestration singletons. Add new domain
behavior to the list; inject side effects through callbacks/interfaces.

The Swift duplicate detector compares twelve meaningful lines with at least
ninety tokens, preserving string literals and ignoring comments. The initial
baseline is a reviewed inventory of legacy clones, not an empty suppression.
CI rejects new or expanded clones and retains all legacy findings. Refactor shared
behavior first. Update individual baseline entries only with an explanation and
maintainer review; never regenerate the baseline merely to make CI green.

TODO/FIXME/HACK comments are exported with live file/line positions. Register each
occurrence under `technical_debt` in `tools/readiness/policies.json` with its exact
file/marker, owner, full GitHub issue URL, review deadline and resolution. The gate
rejects unregistered/copied markers, duplicate or stale registrations, missing
metadata and overdue reviews. Moving a comment does not require pinning its line.
When resolving debt, remove both its comment and registration. Strings are not
debt comments. The five legacy entries are associated with assigned issue #7;
registration does not mean the product problem has been resolved.

Temporary flags require an owner, source symbol, review deadline and explicit
removal condition in `policies.json`. CI detects removed/unreferenced/overdue flags.
The AEC3 escape hatch stays until real-meeting validation supports removal.
User preferences and permanent settings are not temporary flags.

## Privacy and errors

Debug and file log sinks redact authorization, provider secrets, cookies, emails,
home-directory paths and recognized transcript/prompt fields. Redaction is defense
in depth: record counts/timing/model identifiers instead of user text.
Error context includes a per-run random identifier, app/OS version, bounded
redacted breadcrumbs and caller stack frames. It remains on-device.
Fatal-signal handlers write fixed strings only; they do not allocate or run regexes.

No third-party crash service, automatic recording/transcript upload or telemetry
account is enabled by this setup. Production error ingestion and error-to-issue
automation require a separately approved privacy policy, service and credentials.
Use the incident runbooks before requesting a user's sanitized support export.
