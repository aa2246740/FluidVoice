"""Align shared root SwiftPM pins to the authoritative Xcode app graph, without upgrading it."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_LOCK = ROOT / "Fluid.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved"


def synchronize(root, app):
    canonical = {pin["identity"].lower(): pin["state"] for pin in app["pins"]}
    changed = []
    for pin in root["pins"]:
        identity = pin["identity"].lower()
        if identity in canonical and pin["state"] != canonical[identity]:
            pin["state"] = canonical[identity].copy()
            changed.append(identity)
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root_path = ROOT / "Package.resolved"
    root = json.loads(root_path.read_text())
    changed = synchronize(root, json.loads(APP_LOCK.read_text()))
    print("Shared root pins differing from the supported app:", ", ".join(changed) or "none")
    if changed and args.write:
        root_path.write_text(json.dumps(root, indent=2, separators=(",", " : ")) + "\n")
    elif changed:
        raise SystemExit("Review the differences, then run sync_pins.py --write; the Xcode lock will not be modified")


if __name__ == "__main__":
    main()
