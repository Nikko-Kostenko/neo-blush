"""Merge Neo Blush appearance into a closed Vivaldi profile, with backup and undo."""
import argparse
import base64
import copy
import datetime
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
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


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def data_url(path, kind):
    return f"data:{kind};base64," + base64.b64encode(path.read_bytes()).decode()


def read_value(data, key):
    for part in key.split("."):
        if not isinstance(data, dict) or part not in data:
            return {"present": False}
        data = data[part]
    return {"present": True, "value": copy.deepcopy(data)}


def write_value(data, key, record):
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in data:
            if not record["present"]:
                return
            data[part] = {}
        data = data[part]
        if not isinstance(data, dict):
            raise ValueError(f"Unexpected non-object parent for {key}")
    if record["present"]:
        data[parts[-1]] = record["value"]
    else:
        data.pop(parts[-1], None)


def check_closed(root):
    for name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        if os.path.lexists(root / name):
            raise RuntimeError("Close Vivaldi completely before applying the theme. Its profile lock was left intact.")


def definitions(resources):
    """Read the installed browser's own schema, rather than trusting stale keys."""
    raw = json.loads((resources / "prefs_definitions.json").read_text())
    result = {}

    def visit(node, parts):
        if not isinstance(node, dict):
            return
        if "type" in node:
            result[".".join(parts)] = node
            return
        for key, value in node.items():
            if isinstance(value, dict):
                visit(value, parts if key in ("properties", "prefs", "preferences") else parts + [key])

    visit(raw, [])
    if "themes.current" in result:
        result = {"vivaldi." + key: value for key, value in result.items()}
    for key, kind in {
        "vivaldi.themes.current": "string",
        "vivaldi.themes.user": "list",
        "vivaldi.themes.current_buttons": "string",
        "vivaldi.themes.prefer_custom_buttons": "boolean",
    }.items():
        if result.get(key, {}).get("type") != kind:
            raise RuntimeError(f"Installed Vivaldi schema does not support {key}; profile was not changed.")
    return result


def theme_assets(args):
    theme = json.loads(args.theme.read_text())
    symbols = json.loads(args.symbols.read_text())
    theme["buttons"] = {
        button: data_url(args.assets / f"{button}.svg", "image/svg+xml") for button in symbols
    }
    if args.wallpaper.is_file():
        theme["backgroundImage"] = data_url(args.wallpaper, "image/jpeg")
    return theme


def export_theme(args, theme):
    args.state.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = args.state / "Neo-Blush-Liquid-Glass.zip"
    portable = copy.deepcopy(theme)
    portable["buttons"] = {key: f"{key}.svg" for key in theme["buttons"]}
    if args.wallpaper.is_file():
        portable["backgroundImage"] = "background.jpg"
    # This archive is for local use; it contains the user's Apple symbol exports.
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("settings.json", encoded(portable))
        for key in theme["buttons"]:
            archive.write(args.assets / f"{key}.svg", f"{key}.svg")
        if args.wallpaper.is_file():
            archive.write(args.wallpaper, "background.jpg")
    print(f"Theme archive: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", type=Path)
    parser.add_argument("--theme", type=Path, default=Path(__file__).with_name("theme.json"))
    parser.add_argument("--symbols", type=Path, default=Path(__file__).with_name("symbols.json"))
    parser.add_argument("--assets", type=Path, default=Path.home() / ".local/share/vivaldi-neo/icons")
    parser.add_argument("--wallpaper", type=Path, default=Path.home() / ".local/share/wallpapers/macbook-neo-blush.jpg")
    parser.add_argument("--root", type=Path, default=Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "vivaldi")
    parser.add_argument("--state", type=Path, default=Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "vivaldi-neo")
    parser.add_argument("--profile", default="Default")
    parser.add_argument("--if-needed", action="store_true")
    parser.add_argument("--skip-running", action="store_true")
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--undo", type=Path)
    args = parser.parse_args()
    if Path(args.profile).name != args.profile or args.profile in (".", ".."):
        parser.error("--profile must be a profile directory name")
    marker = args.state / f"{args.profile}-applied.json"
    if args.if_needed and not args.undo and marker.exists():
        return
    if args.export_only:
        export_theme(args, theme_assets(args))
        return
    try:
        check_closed(args.root)
    except RuntimeError:
        if args.skip_running:
            print("Neo Blush setup deferred until Vivaldi is closed.")
            return
        raise
    path = args.root / args.profile / "Preferences"
    original = path.read_bytes() if path.exists() else None
    data = json.loads(original) if original is not None else {}
    if data.get("profile", {}).get("exit_type") not in (None, "Normal", "SessionEnded"):
        raise RuntimeError("Open and quit Vivaldi normally before changing this profile.")
    theme = json.loads(args.theme.read_text())
    theme_id = theme["id"]
    current_user = read_value(data, "vivaldi.themes.user").get("value", [])
    if not isinstance(current_user, list):
        raise ValueError("The user themes preference is not a list")
    if args.undo:
        before = json.loads((args.undo / "appearance-before.json").read_text())
        applied = json.loads((args.undo / "appearance-applied.json").read_text())
        # Preserve themes added and preferences changed after this setup.
        previous_themes = before["vivaldi.themes.user"].get("value", [])
        changes = {
            key: record for key, record in before.items()
            if key != "vivaldi.themes.user" and read_value(data, key) == applied[key]
        }
        restored_themes = [item for item in current_user if item.get("id") != theme_id]
        restored_themes += [item for item in previous_themes if item.get("id") == theme_id]
        changes["vivaldi.themes.user"] = {"present": True, "value": restored_themes}
    else:
        if args.resources is None:
            parser.error("--resources must point to the installed Vivaldi UI resources")
        schema = definitions(args.resources)
        theme = theme_assets(args)
        # Start with this browser version's native shape, retaining new fields.
        defaults = schema.get("vivaldi.themes.system", {}).get("default", [])
        template = copy.deepcopy(defaults[0]) if isinstance(defaults, list) and defaults else {}
        template.update(theme)
        changes = {
            # Chromium's Linux SystemTheme enum: GTK=1. The launcher supplies
            # the app-specific GTK palette; Vivaldi's own UI theme stays separate.
            "extensions.theme.system_theme": {"present": True, "value": 1},
            "vivaldi.themes.user": {"present": True, "value": [item for item in current_user if item.get("id") != theme_id] + [template]},
            "vivaldi.themes.current": {"present": True, "value": theme_id},
            "vivaldi.themes.current_buttons": {"present": True, "value": theme_id},
            "vivaldi.themes.prefer_custom_buttons": {"present": True, "value": True},
        }
        schedule = schema.get("vivaldi.theme.schedule.enabled", {})
        enum_values = schedule.get("enum_values", {})
        if isinstance(enum_values, dict) and "off" in enum_values:
            changes["vivaldi.theme.schedule.enabled"] = {"present": True, "value": enum_values["off"]}
        elif schedule:
            print("If system theme scheduling overrides Neo Blush, set Themes > Theme Schedule to No Scheduling.")
        before = {key: read_value(data, key) for key in changes}
        export_theme(args, theme)
    updated = copy.deepcopy(data)
    for key, record in changes.items():
        write_value(updated, key, record)
    backup = args.state / "backups" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup.mkdir(parents=True, mode=0o700)
    if original is not None:
        atomic_write(backup / "Preferences", original)
    atomic_write(backup / "appearance-before.json", encoded({key: read_value(data, key) for key in changes}))
    atomic_write(backup / "appearance-applied.json", encoded(changes))
    check_closed(args.root)
    if (path.read_bytes() if path.exists() else None) != original:
        raise RuntimeError("Vivaldi preferences changed during setup; nothing was applied.")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    atomic_write(path, encoded(updated))
    atomic_write(marker, encoded({"backup": str(backup), "profile": args.profile, "restored": bool(args.undo)}))
    print(f"{'Restored previous appearance' if args.undo else 'Applied Neo Blush'} to {args.profile}. Backup: {backup}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f"Neo Blush: {error}", file=sys.stderr)
        sys.exit(1)
