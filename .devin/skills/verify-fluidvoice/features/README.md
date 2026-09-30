# FluidVoice verification map

This directory is the maintained source for verifying the user-facing behavior of FluidVoice. Read the index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- Launch per the parent SKILL.md: `./build.sh unsigned`, `defaults write com.FluidApp.app.debug OnboardingCompleted -bool true`, `open "DerivedData/Build/Products/Debug/FluidVoice Debug.app"`.
- `pgrep -f "FluidVoice Debug"` returns a pid; a screenshot shows the main window with the "What's New" sheet dismissed.
- Evidence goes to `~/fluidvoice-verify/<timestamp>/`; the directory is created before the first artifact.
- Never drive an instance that was not started by this verification run (single-instance app).

## Driving conventions

- Drive exclusively through the `computer` tool (screenshots, clicks, type). The app exposes no accessibility tree — locate elements by screenshot, read small text with `zoom`.
- Current builds render zh-Hans UI only: match Chinese labels (`云端`, `筛选`, `设置 API Key`, `已连接`, `激活`, `使用中`); English label names in feature files are reference only.
- Start every recipe from the baseline state unless its preconditions say otherwise.
- Click the LEFT half of API-key fields; the adjacent "Get API Key" button opens a browser on stray clicks. Confirm the caret via screenshot before typing — missed clicks drop keystrokes into the sidebar type-ahead and change pages silently.
- Secrets are typed as `${SECRET_NAME}` references, never literals. Key fields are SecureFields and stay masked.
- Restore any state a recipe mutates unless the mutation is itself the proof; never delete proof artifacts during cleanup.

## Proof and skip reporting

- Capture the user action and the resulting state, not only the final screen.
- UI proof = screenshot(s) showing the app window with its identity visible (title bar / sidebar).
- Mutation proof = a second screenshot of the persisted state after the sheet closes or the app re-opens.
- Record the feature ID and entry point used with every artifact (use the file-naming convention in the parent SKILL.md).
- Report an unreachable path with the attempted action and the unmet precondition; do not report a skipped path as verified through a different one.
- Real-microphone dictation is never drivable on a VM — report it untested, do not simulate it.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order: `Sub-features`, `How to get to it (user POV)`, `Driving it with computer-use`, `Gotchas`.

## Features

- [Cloud ASR engine setup](./voice-engine-cloud.md) — Cloud filter lists the three engines, config sheets render per vendor, Test Connection shows the right success/error surface.
- [AI provider verification](./ai-provider-verify.md) — expanding a provider, entering a key, fetching models, and verifying moves it to the verified list.
- [Dictation history](./history-view.md) — the History page lists past dictations with actions; empty state renders correctly.
- [Live dictation](./dictation-hotkey.md) — hotkey-driven recording and insertion; documents why it is not drivable without a microphone and what partial coverage exists.
