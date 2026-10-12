"""Detect repeated Swift code blocks and reject new clones against a reviewed baseline."""

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "tools/readiness/duplicate-baseline.json"
# Strings precede comments so URL literals are not mistaken for comments.
TOKENS = re.compile(r'"""[\s\S]*?"""|"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/|\w+|[^\s]')
WINDOW = 12
MIN_TOKENS = 90


def blocks(text):
    lines = defaultdict(list)
    line = 1
    previous = 0
    for match in TOKENS.finditer(text):
        line += text[previous:match.start()].count("\n")
        token = match.group()
        if not token.startswith(("//", "/*")):
            lines[line].append(token)
        line += token.count("\n")
        previous = match.end()
    meaningful = [(number, tokens) for number, tokens in sorted(lines.items()) if len(tokens) >= 3]
    for index in range(len(meaningful) - WINDOW + 1):
        selected = meaningful[index:index + WINDOW]
        tokens = [token for _, items in selected for token in items]
        if len(tokens) >= MIN_TOKENS:
            fingerprint = hashlib.sha256("\x1f".join(tokens).encode()).hexdigest()
            yield fingerprint, selected[0][0], selected[-1][0]


def scan(root):
    occurrences = defaultdict(list)
    for path in sorted((root / "Sources/Fluid").rglob("*.swift")):
        for fingerprint, start, end in blocks(path.read_text()):
            locations = occurrences[fingerprint]
            name = str(path.relative_to(root))
            if not locations or locations[-1]["file"] != name or start > locations[-1]["end"]:
                locations.append({"file": name, "start": start, "end": end})
    return {key: value for key, value in occurrences.items() if len(value) > 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-baseline", action="store_true", help="Review generated inventory before accepting it")
    args = parser.parse_args()
    clones = scan(ROOT)
    if args.write_baseline:
        if BASELINE.exists():
            raise SystemExit("Baseline already exists; review individual changes instead of replacing it")
        BASELINE.write_text(json.dumps({"owner": "@aa2246740", "clones": clones}, indent=2) + "\n")
    if not BASELINE.exists():
        raise SystemExit("Missing reviewed duplication baseline")
    baseline = json.loads(BASELINE.read_text())["clones"]
    # A third location for a known block is also new duplication.
    new = {
        key: locations for key, locations in clones.items()
        if {item["file"] for item in locations} - {item["file"] for item in baseline.get(key, [])}
        or len(locations) > len(baseline.get(key, []))
    }
    report = {"legacy_clone_blocks": len(clones), "new_clone_blocks": len(new), "new": new, "clones": clones}
    output = ROOT / "quality-artifacts"
    output.mkdir(exist_ok=True)
    (output / "duplication.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Repeated Swift blocks: {len(clones)}; new or expanded blocks: {len(new)}")
    if new:
        raise SystemExit("New duplicate code detected; extract shared behavior or review an explicit baseline change")


if __name__ == "__main__":
    main()
