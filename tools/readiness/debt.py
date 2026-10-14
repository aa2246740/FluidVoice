"""Inventory Swift comment debt and require live, owned work-item registrations."""

import datetime
import re
from collections import Counter

MARKER = re.compile(r"\b(?:TODO|FIXME|HACK)\b")
STRING_OPEN = re.compile(r'(?P<hashes>#+)?(?P<quote>"""|")')
BLOCK_DELIMITER = re.compile(r"/\*|\*/")


def comments(text):
    """Yield comment spans, preserving nested blocks and Swift string boundaries."""
    cursor = 0
    states = [["code", None]]
    while cursor < len(text):
        kind, value = states[-1]
        if kind == "string":
            delimiter, escape = value
            if text.startswith(delimiter, cursor):
                cursor += len(delimiter)
                states.pop()
            elif text.startswith(escape, cursor):
                cursor += len(escape)
                if text.startswith("(", cursor):
                    states.append(["interpolation", 1])
                cursor += 1
            else:
                cursor += 1
            continue
        if text.startswith("//", cursor):
            end = text.find("\n", cursor)
            end = len(text) if end < 0 else end
            yield cursor, end
            cursor = end
        elif text.startswith("/*", cursor):
            start, depth = cursor, 1
            cursor += 2
            while depth:
                delimiter = BLOCK_DELIMITER.search(text, cursor)
                if not delimiter:
                    cursor = len(text)
                    break
                depth += 1 if delimiter.group() == "/*" else -1
                cursor = delimiter.end()
            yield start, cursor
        else:
            opening = STRING_OPEN.match(text, cursor)
            if opening:
                hashes = opening.group("hashes") or ""
                states.append(["string", (opening.group("quote") + hashes, "\\" + hashes)])
                cursor = opening.end()
            else:
                if kind == "interpolation":
                    if text[cursor] == "(":
                        states[-1][1] += 1
                    elif text[cursor] == ")":
                        states[-1][1] -= 1
                        if states[-1][1] == 0:
                            states.pop()
                cursor += 1


def inventory(root):
    debt = []
    for path in sorted((root / "Sources/Fluid").rglob("*.swift")):
        text = path.read_text()
        line, previous = 1, 0
        for start, end in comments(text):
            line += text.count("\n", previous, start)
            comment = text[start:end]
            for number, body in enumerate(comment.splitlines(), line):
                marker = MARKER.search(body)
                if marker:
                    debt.append({
                        "file": str(path.relative_to(root)), "line": number,
                        "marker": body[marker.start():].removesuffix("*/").strip(),
                        "linked_issue": False,
                    })
            line += comment.count("\n")
            previous = end
    return debt


def verify(root, policy, today=None):
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    registered = {}
    for entry in policy.get("technical_debt", []):
        for field in ("file", "marker", "owner", "issue", "review_by", "resolution"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError(f"Technical debt requires {field}")
        if not re.fullmatch(r"@[A-Za-z0-9][A-Za-z0-9-]*", entry["owner"]):
            raise ValueError("Technical debt requires a GitHub owner")
        if not re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+/issues/[1-9]\d*", entry["issue"]):
            raise ValueError("Technical debt requires an explicit issue URL, not a bare PR reference")
        if today >= datetime.date.fromisoformat(entry["review_by"]):
            raise ValueError(f"Technical debt review overdue: {entry['file']} ({entry['owner']})")
        key = (entry["file"], entry["marker"])
        if key in registered:
            raise ValueError(f"Duplicate debt policy: {key}")
        registered[key] = entry
    report = inventory(root)
    found = Counter((item["file"], item["marker"]) for item in report)
    for key, count in found.items():
        if key not in registered or count != 1:
            raise ValueError(f"Unregistered technical debt occurrence: {key} (count={count})")
    for key in registered.keys() - found.keys():
        raise ValueError(f"Stale debt policy: {key}")
    for item in report:
        entry = registered[(item["file"], item["marker"])]
        item.update({field: entry[field] for field in ("owner", "issue", "review_by", "resolution")})
        item["linked_issue"] = True
    return report
