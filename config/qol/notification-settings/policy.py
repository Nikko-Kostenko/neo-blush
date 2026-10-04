"""Local notification preferences, layered over Home Manager's SwayNC config."""

from contextlib import contextmanager
from pathlib import Path
import fcntl
import json
import os
import re
import tempfile

STATES = ("enabled", "muted", "ignored")


def state_dir():
    return Path(os.environ.get("NEO_NOTIFICATION_STATE_DIR", str(
        Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
        / "neo-notifications")))


def runtime_config():
    return Path(os.environ["XDG_RUNTIME_DIR"]) / "neo-notifications/config.json"


def base_config():
    return Path(os.environ.get("NEO_NOTIFICATION_BASE_CONFIG", str(
        Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        / "swaync/config.json")))


def read_json(path, default):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def locked():
    directory = state_dir()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / ".lock").open("a") as stream:
        os.chmod(stream.name, 0o600)
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield directory


def preferences():
    data = read_json(state_dir() / "preferences.json", {"default": "enabled", "apps": {}})
    if not isinstance(data, dict) or data.get("default") not in STATES:
        raise ValueError("Invalid notification preferences")
    if not isinstance(data.get("apps"), dict) or any(v not in STATES for v in data["apps"].values()):
        raise ValueError("Invalid application preferences")
    return data


def save_preference(name, state):
    if state not in (*STATES, "default") or (name is None and state == "default"):
        raise ValueError("Unknown delivery mode")
    with locked() as directory:
        data = preferences()
        if name is None:
            data["default"] = state
        elif state == "default":
            data["apps"].pop(name, None)
        else:
            data["apps"][name] = state
        atomic_json(directory / "preferences.json", data)


def record_app(name, desktop_entry):
    # Store sender identity only, never notification titles, bodies or actions.
    if not isinstance(name, str) or len(name) > 512:
        return False
    if not isinstance(desktop_entry, str) or len(desktop_entry) > 512:
        desktop_entry = ""
    with locked() as directory:
        apps = read_json(directory / "applications.json", {})
        if apps.get(name) != {"desktop-entry": desktop_entry}:
            apps[name] = {"desktop-entry": desktop_entry}
            atomic_json(directory / "applications.json", apps)
    return False


def compose(base, prefs):
    config = dict(base)
    rules = {}
    # Specific interactive choices precede declarative rules; regex metacharacters
    # in sender names are literal. Keep the default catch-all last.
    for index, (name, state) in enumerate(sorted(prefs["apps"].items())):
        rules[f"neo-app-{index:04d}"] = {"app-name": "^" + re.escape(name) + "$", "state": state}
    for index, rule in enumerate(base.get("notification-visibility", {}).values()):
        rules[f"configured-{index:04d}"] = rule
    if prefs["default"] != "enabled":
        rules["neo-default"] = {"app-name": ".*", "state": prefs["default"]}
    if rules:
        config["notification-visibility"] = rules
    else:
        config.pop("notification-visibility", None)
    return config


def apply():
    with locked():
        atomic_json(runtime_config(), compose(read_json(base_config(), {}), preferences()))


def applications():
    data = read_json(state_dir() / "applications.json", {})
    for name in preferences()["apps"]:
        data.setdefault(name, {"desktop-entry": ""})
    return data
