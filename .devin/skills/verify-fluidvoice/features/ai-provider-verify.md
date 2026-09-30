# AI provider verification

The AI Providers page lists the services that power text enhancement. Expanding a provider reveals a config card (API key, Get API Key link, model picker); entering a valid key and verifying the model moves the provider into a "Verified providers" section with a green checkmark.

## Sub-features

- `provider-list` — the "All providers" list shows ~10 built-in providers including "Alibaba Bailian (Qwen)".
- `expand-config` — clicking a row expands an inline card with a SecureField key input, Get API Key link, and model picker.
- `model-fetch` — the refresh (`arrow.clockwise`) button populates the picker from the live `/models` endpoint.
- `verify-model` — "Verify model" issues a real request; success moves the provider to "Verified providers (N)" with a green check and "Use as default" / Edit controls.

## How to get to it (user POV)

- Sidebar → Configure → AI Providers → scroll the "All providers" list → click the "Alibaba Bailian (Qwen)" row.

## Driving it with computer-use

Preconditions: app launched per baseline; `${BAILIAN_DASHSCOPE_API_KEY}` available.

- **Locate provider:** scroll the list until "Alibaba Bailian (Qwen)" (purple AB logo, between OpenRouter and Ollama) is visible → click the row → screenshot: expanded card.
- **Enter key:** click LEFT half of the key field → confirm caret → type `${BAILIAN_DASHSCOPE_API_KEY}` (stays masked) → screenshot of masked field.
- **Fetch models:** click the `arrow.clockwise` button → model picker fills (e.g. auto-selects a model) → screenshot.
- **Verify:** click "Verify model" → success banner/state → screenshot: provider listed under "Verified providers (1)" with green checkmark.

## Gotchas

- The model dropdown may not visibly open on click — an auto-selected model is sufficient for verification.
- A failed verify leaves the provider in the unverified list with red text — capture that state instead of retrying blindly.
- The expanded card collapses if you click the row again — screenshot before re-clicking.
