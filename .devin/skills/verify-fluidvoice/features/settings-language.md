# App display language

The app ships two localizations: `en` (declared development region — English resolves through the source strings, no `en.lproj` exists) and `zh-Hans`. Settings → General has a Language row letting the user pick `System Default`, `English`, or `简体中文`; the choice applies on the next launch.

## Sub-features

- `language-row` — the row renders between the Volume slider and Automatic Updates in the General card, titled `Language`/`语言` with a restart hint.
- `picker-options` — the menu lists exactly three items; item labels localize with the current UI language (zh UI shows `跟随系统`/`英文`/`简体中文`, en UI shows `System Default`/`English`/`简体中文`).
- `switch-language` — selecting a value writes `AppLanguage` and `AppleLanguages` in `com.FluidApp.app.debug` defaults; relaunching renders the whole app in the new language.
- `follow-system` — `System Default` removes the `AppleLanguages` override so the app follows the macOS locale again.

## How to get to it (user POV)

- Sidebar → Settings/设置 → General/通用 → `Language`/`语言` row → picker on the right.

## Driving it with computer-use

Preconditions: app launched per baseline.

- **Locate the row:** Settings → General → screenshot the row + picker showing the current value.
- **Open the menu:** click the picker → screenshot the three options (a first click may only highlight — click the item again if the menu stays open).
- **Verify persistence:** after choosing, run `defaults read com.FluidApp.app.debug AppleLanguages` and `defaults read com.FluidApp.app.debug AppLanguage` in the shell — expect `("zh-Hans")`/`zh-Hans` or `(en)`/`en`.
- **Verify apply:** quit via `osascript -e 'quit app "FluidVoice Debug"'`, relaunch with `open`, screenshot the dashboard — menu bar and sidebar must render in the new language.
- **Restore:** set the picker back to the user's preferred language (zh-Hans for this fork's owner) and relaunch once more; screenshot the restored state.

## Gotchas

- The change never applies in-process — proof of a switch requires an actual relaunch, not just the picker label changing.
- `System Default` removes the `AppleLanguages` key entirely (`defaults read` then errors "does not exist" — that IS the expected state).
- Shell-side `defaults write … AppleLanguages` is honored again since `CFBundleDevelopmentRegion=en` was declared; it is equivalent to the picker but does not set `AppLanguage` (the picker reads `AppLanguage` only — a shell-forced language leaves the picker showing its previous choice until the app rewrites it).
- The `AppLanguage` and `AppleLanguages` keys persist across launches and rebuilds — check them first if the app renders an unexpected language.
