#!/usr/bin/env bash
# Activate the menu bar for the current user without rebuilding NixOS.
set -euo pipefail
NEO_THEME_REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
menu_state="${XDG_STATE_HOME:-$HOME/.local/state}/neo-menu-bar"
mkdir -p "$menu_state/backup"
for menu_file in config style.css; do
  if [[ ! -e "$menu_state/backup/$menu_file" ]]; then
    cp -a "$HOME/.config/waybar/$menu_file" "$menu_state/backup/$menu_file"
  fi
done
nix build "path:$NEO_THEME_REPO#neo-python" \
  --out-link "$menu_state/python"
nix build "path:$NEO_THEME_REPO#neo-dynamic-island" \
  --out-link "$menu_state/island"
nix build "path:$NEO_THEME_REPO#neo-waybar" \
  --out-link "$menu_state/waybar"
mkdir -p "$HOME/.local/bin"
ln -sfn "$(readlink -f "$menu_state/island")/bin/neo-dynamic-island" "$HOME/.local/bin/neo-dynamic-island"
"$menu_state/python/bin/python3" - "$NEO_THEME_REPO" "$HOME" "$menu_state" <<'PY'
import json
from pathlib import Path
import sys

repo, home, state = map(Path, sys.argv[1:])
config = json.loads((repo / "config/waybar/config.json").read_text())
config["custom/control"]["on-click-release"] = str(home / ".local/bin/neo-control-center")
icons = home / ".local/share/neo-menu-bar/icons"
icons.mkdir(parents=True, exist_ok=True)
local = home / ".local/share/neo-control-center/icons"
fallback = repo / "config/waybar/control-center/icons/neo-wifi-symbolic.svg"
for target, source in [("wifi", "wifi"), ("wifi-off", "wifi-off"), ("network", "network")]:
    asset = local / f"neo-{source}-symbolic.svg"
    data = (asset if asset.exists() else fallback).read_text()
    if target in {"wifi", "wifi-off"}:
        # SF Wi-Fi has more internal whitespace than the other status symbols.
        # Enlarge its outline by 18% while keeping the tray slot centered.
        data = data.replace('viewBox="0 0 24 24"', 'viewBox="1.8 1.8 20.4 20.4"', 1)
    (icons / f"{target}.svg").write_text(data.replace("#000000", "#452c3b").replace("#2e3436", "#452c3b"))
bluetooth = (repo / "config/waybar/assets/bluetooth.svg").read_text()
(icons / "bluetooth.svg").write_text(bluetooth)
(icons / "bluetooth-off.svg").write_text(bluetooth.replace("#452c3b", "#87697c"))
config["tray"]["icons"] = {key: value.replace("~/", str(home) + "/", 1)
                            for key, value in config["tray"]["icons"].items()}
for key, value in config.get("custom/island", {}).items():
    if isinstance(value, str) and value.startswith("neo-dynamic-island"):
        config["custom/island"][key] = str(home / ".local/bin") + "/" + value
for module in config.values():
    if isinstance(module, dict) and "menu-file" in module:
        module["menu-file"] = module["menu-file"].replace("~/", str(home) + "/", 1)
(state / "config.json").write_text(json.dumps([config], ensure_ascii=False, indent=2) + "\n")
(state / "style.css").write_text((repo / "config/waybar/style.css").read_text())
PY
ln -sfn "$menu_state/config.json" "$HOME/.config/waybar/config"
ln -sfn "$menu_state/style.css" "$HOME/.config/waybar/style.css"
if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
  systemctl --user stop neo-waybar-control-center.service neo-waybar-pyglass.service 2>/dev/null || true
  pkill -u "$UID" -TERM -x 'waybar|\.waybar-wrapped' || true
  systemd-run --user --unit=neo-waybar-control-center --collect \
    --setenv="WAYLAND_DISPLAY=$WAYLAND_DISPLAY" \
    --setenv="DISPLAY=${DISPLAY:-}" --setenv="XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR" \
    "$menu_state/waybar/bin/waybar" -c "$HOME/.config/waybar/config" \
    -s "$HOME/.config/waybar/style.css"
fi
printf 'Menu bar activated. Backup: %s/backup\n' "$menu_state"
