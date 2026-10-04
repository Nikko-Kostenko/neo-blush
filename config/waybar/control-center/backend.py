"""Desktop controls. Commands use argument lists and never a shell."""

import os
from pathlib import Path
import re
import subprocess


def command(*args, timeout=3):
    try:
        result = subprocess.run(args, text=True, capture_output=True, timeout=timeout,
                                env={**os.environ, "LC_ALL": "C"})
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"{args[0]}: {error}") from error
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip()
                           or f"{args[0]} failed")
    return result.stdout.strip()


def query(*args):
    try:
        return command(*args)
    except RuntimeError:
        return None


def volume(target):
    output = query("wpctl", "get-volume", target)
    match = re.search(r"Volume:\s+([0-9.]+)", output or "")
    if not match:
        return None
    return {"value": min(100, round(float(match[1]) * 100)),
            "muted": "[MUTED]" in output}


def battery():
    for device in sorted(Path("/sys/class/power_supply").glob("*")):
        try:
            if (device / "type").read_text().strip() == "Battery":
                capacity = (device / "capacity").read_text().strip()
                status = (device / "status").read_text().strip()
                return f"{capacity}% · {status}"
        except OSError:
            continue
    return ""


def media():
    players = (query("playerctl", "--list-all") or "").splitlines()
    selected = None
    for player in players:
        status = query("playerctl", f"--player={player}", "status")
        if status and (selected is None or status == "Playing"):
            selected = {"player": player, "status": status}
        if status == "Playing":
            break
    if selected:
        option = f"--player={selected['player']}"
        selected["title"] = query("playerctl", option, "metadata", "xesam:title") or "Media"
        selected["artist"] = query("playerctl", option, "metadata", "xesam:artist") or selected["player"]
    return selected


def read_state():
    wifi_radio = query("nmcli", "radio", "wifi")
    devices = query("nmcli", "-t", "--escape", "no", "-f", "TYPE,STATE,CONNECTION",
                    "device", "status")
    wifi = {"enabled": None, "text": "Unavailable"}
    wifi_devices = [line.split(":", 2) for line in (devices or "").splitlines()
                    if line.startswith("wifi:")]
    if wifi_devices and wifi_radio in ("enabled", "disabled"):
        wifi["enabled"] = wifi_radio == "enabled"
        wifi["text"] = "Not connected" if wifi["enabled"] else "Off"
        for fields in wifi_devices if wifi["enabled"] else []:
            if len(fields) == 3 and fields[1] == "connected":
                wifi["text"] = fields[2]
                break

    bluetooth = {"enabled": None, "text": "No adapter"}
    info = query("bluetoothctl", "show")
    powered = re.search(r"Powered:\s+(yes|no)", info or "")
    if powered:
        bluetooth["enabled"] = powered[1] == "yes"
        connected = (query("bluetoothctl", "devices", "Connected") or "") if bluetooth["enabled"] else ""
        names = [line.split(" ", 2)[2] for line in connected.splitlines()
                 if line.startswith("Device ") and len(line.split(" ", 2)) == 3]
        bluetooth["text"] = ", ".join(names) if names else ("On" if bluetooth["enabled"] else "Off")

    brightness = None
    info = query("brightnessctl", "--class=backlight", "--machine-readable")
    if info:
        fields = info.splitlines()[0].split(",")
        if len(fields) >= 4 and fields[3].endswith("%"):
            try:
                brightness = int(fields[3][:-1])
            except ValueError:
                pass

    return {
        "wifi": wifi, "bluetooth": bluetooth, "brightness": brightness,
        "sound": volume("@DEFAULT_AUDIO_SINK@"),
        "microphone": volume("@DEFAULT_AUDIO_SOURCE@"),
        "media": media(), "battery": battery(),
        "awake": query("systemctl", "--user", "is-active", "neo-keep-awake.service") == "active",
    }


def awake_command(enabled):
    if enabled:
        return ["systemctl", "--user", "stop", "neo-keep-awake.service"]
    return ["systemd-run", "--user", "--unit=neo-keep-awake", "--collect",
            "systemd-inhibit", "--what=idle:sleep", "--mode=block",
            "--who=Control Center", "--why=Keep Awake is enabled", "sleep", "infinity"]
