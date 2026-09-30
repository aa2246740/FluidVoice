# Live dictation

Pressing the configured hotkey starts recording, transcribes with the active speech engine, and inserts the result into the focused app. This is the product's core path — and the one a VM cannot drive, because there is no microphone. This file documents what a human verifies on real hardware and the partial coverage available on a VM.

## Sub-features

- `hotkey-toggle` — the configured global hotkey starts/stops a recording session.
- `overlay-state` — the notch/overlay shows listening → transcribing → done states.
- `insertion` — the transcript lands in the focused text field via the paste coordinator.
- `engine-fallback` — with no engine configured the overlay surfaces the missing-setup error.

## How to get to it (user POV)

- Any app → press the dictation hotkey (default configurable in Settings → Shortcuts) → speak → press again or auto-stop.

## Driving it with computer-use

Preconditions: a REAL microphone and Accessibility/Input-Monitoring permissions — not satisfiable on a VM. Do not attempt on headless machines; report untested.

- **On real hardware (manual recipe for a human tester):** focus a text field (e.g. TextEdit) → press the hotkey → screenshot the recording overlay → speak a sentence → stop → screenshot: transcript inserted into the field.
- **VM-partial coverage:** the overlay's idle/error states can be screenshotted from the settings preview, and `CloudASRProvider.transcribe` is exercised end-to-end by `Tests/run_cloud_asr_client_tests.sh` with a real key — cite that as the substitute evidence, clearly labeled.

## Gotchas

- Never simulate dictation by scripting key events against a VM with no audio device — a silent "transcript" proves nothing and has misled past runs.
- The app needs Accessibility + Microphone permissions on real hardware; the unsigned debug build re-prompts after every rebuild.
- `transcribeStreaming` for cloud engines intentionally returns empty (billing guard); silence ≠ broken — only the final-pass call hits the network.
