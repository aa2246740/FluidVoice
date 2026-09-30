---
name: verify-fluidvoice
description: Drive the FluidVoice macOS dictation app's real UI to prove settings and engine behavior — launch the unsigned debug build, exercise a feature like a user, capture screenshot evidence. Reach for it when a change touches Voice Engine, AI Providers, dictation, or any visible settings surface.
---

# Verify FluidVoice

FluidVoice is a macOS menu-bar SwiftUI/AppKit dictation app. This skill drives the real app via computer-use (screenshots + clicks — the app exposes no accessibility tree) and captures visual proof. Read `features/README.md` for the feature map before driving; each feature file is a self-contained recipe.

## Launch

```bash
cd ~/repos/FluidVoice
osascript -e 'quit app "FluidVoice Debug"' 2>/dev/null   # quit any leftover instance first
./build.sh unsigned                     # → DerivedData/Build/Products/Debug/FluidVoice Debug.app
defaults write com.FluidApp.app.debug OnboardingCompleted -bool true   # skip onboarding once per VM
open "DerivedData/Build/Products/Debug/FluidVoice Debug.app"
```

Ready check: `pgrep -f "FluidVoice Debug"` returns a pid AND a screenshot shows the main window (dismiss the "What's New" sheet with its X first). To enlarge the window use the macOS Window → Zoom menu — double-clicking the title bar does not zoom this build.

**UI language:** the app is bilingual — `en` (declared development region, resolves via source strings) and `zh-Hans`. Settings → General/通用 has a Language/语言 row with `System Default`/`跟随系统`, `English`, `简体中文`; an explicit choice writes the per-app `AppleLanguages` + `AppLanguage` defaults and applies on the NEXT launch. `defaults write com.FluidApp.app.debug AppleLanguages` also works again for forcing a language from the shell. Match labels against whichever language the running instance renders — feature files list both (`云端`="Cloud", `设置 API Key`="Set API Key", `已连接`="Connected", `激活`="Activate", `使用中`="Active").

Single-instance app — never launch a second copy or drive an instance you did not start.

## Doctor

Run when anything looks off, before driving:

```bash
pgrep -fl "FluidVoice Debug"                              # process up?
defaults read com.FluidApp.app.debug OnboardingCompleted  # must print 1, else onboarding will block
ls -la "DerivedData/Build/Products/Debug/FluidVoice Debug.app/Contents/MacOS/"  # build exists & fresh
```

Then screenshot: window present, no modal error sheet. If the build is stale or missing, rebuild; do not drive a stale binary.

## Drive

- **Harness:** the `computer` tool only — screenshots to find elements, `left_click`/`type`/`key` to act, `zoom` on regions to read small text. No DOM, no accessibility tree.
- **Navigation map:** all settings live in the main window's left sidebar (no Preferences window). "Voice Engine" and "AI Providers" sit under "Configure".
- Voice Engine → Speech Recognition card → "Filter: All" / `筛选：全部` dropdown → "Cloud" / `云端` shows the three cloud engines (Volcengine Doubao ASR, Qwen3-ASR Flash, Fish Audio ASR). A row shows "Set API Key" / `设置 API Key` without credentials, "Activate" / `激活` with them; either opens the vendor config sheet.
- Entering keys: click the LEFT half of the key field (the "Get API Key" button hugs its right edge — a stray click opens Safari). Screenshot to confirm the caret BEFORE typing; a missed click sends keystrokes to the sidebar's type-ahead and silently changes pages. All key fields are SecureFields — screenshots stay safe. Type secrets as `${SECRET_NAME}` references, never literals.
- Expected error surfaces (invalid key): DashScope/Fish Audio → red `HTTP 401` text; Volcengine → red `error 45000010`; success → green `Connected. Response: <text>` / `已连接。响应：<text>`.
- AI Providers → expand a provider row → enter key → click the `arrow.clockwise` button → model picker fills from live `/models` → "Verify model" → provider moves to "Verified providers (N)" with a green checkmark.
- When credentials are already saved, the config sheet opens with the key prefilled (masked) and Test Connection enabled — the empty-field disabled state only applies to a first-time setup.
- Saving the config of an engine that is already active de-activates it (the "Active"/`使用中` badge drops and the row offers `激活` again until you re-activate it — known app quirk, screenshot the state either way).
- Menus and sidebar rows frequently need a second click: a first click on a sidebar item can merely focus the window, and a first click on a popup-menu item can highlight it without committing — screenshot after each click and click again if the state did not change.
- Real dictation (hotkey + live mic) is NOT drivable on a VM — no microphone. Mark it untested; do not fake it.

## Evidence

Write all artifacts to `~/fluidvoice-verify/<timestamp>/` (outside the repo — never commit them):

- Screenshot of the state BEFORE the user action and AFTER it — action + resulting state, not just the final screen.
- For mutation flows (key saved, provider verified, engine activated): a second screenshot of the persisted state (e.g. the "Active" badge, "Verified providers" section) after the sheet closes.
- Record the feature id and entry point used next to each artifact (name files `voice-engine-cloud_set-api-key_after.png`, etc.).
- A run that could not reach a path is reported with the attempted action and the unmet precondition — never reported as verified.

## Cleanup

```bash
osascript -e 'quit app "FluidVoice Debug"' 2>/dev/null || kill "$(pgrep -f 'FluidVoice Debug' | head -1)"
```

Only tear down the instance this run started. Evidence in `~/fluidvoice-verify/` survives cleanup — after quitting, confirm the files still exist (`ls ~/fluidvoice-verify/<timestamp>/`). A cleanup that eats proof fails the run.

## Helpers

None — every step is a shell one-liner or a `computer` action shown above.
