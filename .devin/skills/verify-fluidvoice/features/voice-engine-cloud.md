# Cloud ASR engine setup

The Voice Engine page lets the user pick a speech-recognition model. Under the "Cloud" filter, three API-key-driven engines appear — Volcengine Doubao ASR, Qwen3-ASR Flash (Alibaba Bailian), and Fish Audio ASR — each opening a vendor-specific config sheet with a Test Connection button that hits the real vendor API.

## Sub-features

- `cloud-filter` — Filter dropdown offers "Cloud"; selecting it shows exactly the three cloud engines.
- `config-sheet` — clicking a row opens a sheet titled with the vendor; fields differ per vendor (Volcengine: App ID/Access Token/Resource ID; Bailian: API Key + Region picker; Fish Audio: API Key only).
- `test-connection-invalid` — a wrong key produces red inline error text and no crash.
- `test-connection-valid` — a real key produces a green "Connected"/`已连接` line; Save activates the engine ("Active"/`使用中` badge under "Active Model").

## How to get to it (user POV)

- Sidebar → Configure → Voice Engine → Speech Recognition card → "Filter"/`筛选` dropdown → "Cloud"/`云端`.
- Each engine row → "Set API Key"/`设置 API Key` (no credentials) or "Activate"/`激活` (credentials saved) → config sheet.

## Driving it with computer-use

Preconditions: app launched per baseline; no saved cloud credentials (for the error-path recipe).

- **List engines:** click the `筛选：全部`/"Filter: All" dropdown → click `云端`/"Cloud" → screenshot: exactly three rows, each with key icon + `设置 API Key`/"Set API Key" (rows with saved credentials show `激活` + `使用中` badge instead).
- **Open a sheet:** click the row action on the Qwen3-ASR row → screenshot: sheet titled "Alibaba Bailian Qwen3-ASR"/`阿里云百炼 Qwen3-ASR` with Get API Key link, Region picker, Model/Language/Endpoint fields; Test Connection disabled only when the key field is empty — a previously saved key comes prefilled (masked) with the button enabled.
- **Invalid-key path:** click LEFT half of key field → confirm caret → type `test-invalid-key` → click Test Connection → within ~2s a red line appears (DashScope: `HTTP 401 ... Incorrect API key`); screenshot.
- **Valid-key path:** select-all + retype `${BAILIAN_DASHSCOPE_API_KEY}` → Test Connection → green `已连接。响应：<text>`/`Connected. Response: <text>` → screenshot → click Save → screenshot: row under "Active Model" with green "Active"/`使用中` badge.
- **Save-on-active quirk:** saving the config of an already-active engine drops it back to a plain `激活` button (the provider resets without re-preparing) — screenshot that state, then click `激活` to restore the `使用中` badge and screenshot again. This is a known app quirk, not a driver error.
- **Volcengine variant:** same flow on the Volcengine row; invalid key shows red `error 45000010: Invalid X-Api-Key`.

## Gotchas

- The "Get API Key" button sits immediately right of the key field — click the field's LEFT half only.
- A missed click drops typing into the sidebar type-ahead and changes the page silently; always confirm the caret first.
- The app ships zh-Hans only in current builds — match Chinese labels (`云端`, `设置 API Key`, `已连接。响应：`, `使用中`, `激活`); English names in this file are reference only.
- Without a real vendor key only the error path is verifiable — report the success path untested rather than faking it.
- Saving a real key writes it to the macOS Keychain (service `com.fluidvoice.cloud-asr-keys`) and activates the engine; that activation is the mutation proof — screenshot the badge.
