# Dictation history

The History page lists previous dictations newest-first with per-entry actions (copy, re-paste, delete). With no dictations it shows a designed empty state. On a VM with no microphone the list will be empty or seeded — either state is verifiable.

## Sub-features

- `list-renders` — the page renders a scrollable list or the empty-state prompt without errors.
- `entry-actions` — selecting an entry shows its transcript and action buttons.
- `persistence` — entries survive an app relaunch (mutations only — skip if empty).

## How to get to it (user POV)

- Sidebar → History (under the main section, above Configure).

## Driving it with computer-use

Preconditions: app launched per baseline.

- **Open page:** click "History" in the sidebar → screenshot: list or empty state fully rendered.
- **Entry detail (if entries exist):** click the first row → screenshot: transcript text and action buttons visible.
- **Empty state (if none):** screenshot the empty-state copy — it must be a designed view, not a blank pane or an error.

## Gotchas

- This page reads local history only — cloud/ASR configuration is irrelevant; do not change engine settings for this recipe.
- Deleting entries to "test" the empty state destroys real user history — never delete as part of verification.
- Timestamps render in the locale of the app language; zh-Hans runs show Chinese date formats — that is correct, not a bug.
