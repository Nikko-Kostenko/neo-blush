"""Apply or undo Brave appearance preferences while the browser is closed."""

import argparse
import copy
import datetime
import json
import os
from pathlib import Path
import sys
import tempfile


MISSING = {"present": False}


def read_value(data, key):
    for part in key.split("."):
        if not isinstance(data, dict) or part not in data:
            return MISSING.copy()
        data = data[part]
    return {"present": True, "value": data}


def write_value(data, key, value):
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in data:
            if not value["present"]:
                return
            data[part] = {}
        data = data[part]
        if not isinstance(data, dict):
            raise ValueError(f"Unexpected non-object parent for {key}")
    if value["present"]:
        data[parts[-1]] = value["value"]
    else:
        data.pop(parts[-1], None)


def check_closed(root, profile):
    # Chromium owns these locks, including broken symlinks. Never delete them.
    for name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        if os.path.lexists(root / name):
            raise RuntimeError("Close Brave completely, then run brave-neo-apply again.")
    prefs = json.loads((profile / "Preferences").read_text())
    if prefs.get("profile", {}).get("exit_type") not in (None, "Normal", "SessionEnded"):
        raise RuntimeError("Open and quit Brave normally before changing its preferences.")


def atomic_write(path, content):
    # Files may contain profile data: retain private permissions.
    fd, temporary = tempfile.mkstemp(prefix=".neo-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", type=Path, default=Path(__file__).with_name("appearance.json"))
    parser.add_argument("--root", type=Path, default=Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "BraveSoftware/Brave-Browser")
    parser.add_argument("--state", type=Path, default=Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "brave-neo")
    parser.add_argument("--profile", default="Default")
    parser.add_argument("--if-needed", action="store_true")
    parser.add_argument("--skip-running", action="store_true")
    parser.add_argument("--undo", type=Path, help="Restore only appearance keys from a backup directory")
    args = parser.parse_args()
    if Path(args.profile).name != args.profile or args.profile in (".", ".."):
        parser.error("--profile must be a profile directory name")
    profile = args.root / args.profile
    marker = args.state / f"{args.profile}-applied.json"
    if args.if_needed and not args.undo and marker.exists():
        print(f"Initial Brave appearance setup already handled for {args.profile}.")
        return
    if not (profile / "Preferences").is_file():
        print(f"No existing Brave profile at {profile}; open Brave once, then run brave-neo-apply.")
        return
    try:
        check_closed(args.root, profile)
    except RuntimeError as error:
        if not args.skip_running:
            raise
        print(f"Brave appearance deferred: {error}")
        return

    settings = json.loads(args.settings.read_text())
    previous = json.loads((args.undo / "appearance-before.json").read_text()) if args.undo else {}
    paths = {"Preferences": profile / "Preferences", "Local State": args.root / "Local State"}
    originals, changes, before = {}, {}, {}
    for name, keys in settings.items():
        path = paths[name]
        originals[name] = path.read_bytes()
        data = json.loads(originals[name])
        before[name] = {key: read_value(data, key) for key in keys}
        updated = copy.deepcopy(data)
        for key, value in keys.items():
            write_value(updated, key, previous[name][key] if args.undo else {"present": value is not None, "value": value})
        changes[name] = (json.dumps(updated, ensure_ascii=False, separators=(",", ":")) + "\n").encode()

    backup = args.state / "backups" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup.mkdir(parents=True, mode=0o700)
    for name, original in originals.items():
        atomic_write(backup / name, original)
    atomic_write(backup / "appearance-before.json", json.dumps(before, indent=2).encode())

    check_closed(args.root, profile)
    for name, path in paths.items():
        if path.read_bytes() != originals[name]:
            raise RuntimeError("Brave preferences changed during setup; nothing was applied. Close Brave and retry.")
    written = []
    try:
        for name, path in paths.items():
            atomic_write(path, changes[name])
            written.append(name)
    except OSError:
        for name in written:
            atomic_write(paths[name], originals[name])
        raise
    if args.undo:
        # Keep setup handled so the launcher does not immediately reapply it.
        atomic_write(marker, json.dumps({"restored": True, "backup": str(args.undo), "profile": args.profile}).encode())
        print("Previous appearance restored. Open Brave to see it.")
    else:
        atomic_write(marker, json.dumps({"backup": str(backup), "profile": args.profile}).encode())
        print("Neo Blush appearance saved: light blush colors, compact horizontal tabs, rounded content and a quieter toolbar.")
        print("Open Brave to see the changes.")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f"brave-neo-apply: {error}", file=sys.stderr)
        sys.exit(1)
