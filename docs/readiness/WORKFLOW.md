# Development and quality workflow

## Validation environments

- Command Line Tools: `python3 tools/readiness/standalone.py` and
  `sh Tests/run_history_persistence_tests.sh`. These execute production behavior
  and isolated fixtures; they do not build the app or prove microphone operation.
- Repository tooling: `python3 tools/readiness/check.py`,
  `python3 tools/readiness/duplicates.py`, and
  `python3 -m unittest discover -s Tests/Readiness -p 'test_*.py' -v`.
- `.devcontainer/devcontainer.json` supplies Python tooling for repository
  automation. Linux containers cannot run macOS, Xcode, SwiftUI or audio acceptance.
  Do not download a local container image on a space-constrained Mac without asking.
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

TODO/FIXME/HACK inventories are exported with file/line positions and issue-link
status on each check. New debt should reference a tracked issue and owner.
Review unlinked legacy markers during triage; the scanner does not pretend these
markers have already been resolved.

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
