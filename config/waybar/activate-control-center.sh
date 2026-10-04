#!/usr/bin/env bash
# Activate just the Control Center as the desktop user, without a system rebuild.
set -euo pipefail

NEO_THEME_REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
center_state="${XDG_STATE_HOME:-$HOME/.local/state}/neo-control-center"
mkdir -p "$center_state" "$HOME/.local/bin"

center_system=$(nix eval --impure --raw --expr builtins.currentSystem)
center_ref="path:$NEO_THEME_REPO#packages.$center_system.neo-control-center"
nix build "$center_ref" --out-link "$center_state/package"
"$center_state/package/bin/neo-control-center" --self-test
center_python=$(nix eval --raw "$center_ref.python.outPath")

mkdir -p "$center_state/backup"
if [[ ! -e "$center_state/backup/waybar-config" ]]; then
  cp -a "$HOME/.config/waybar/config" "$center_state/backup/waybar-config"
  if [[ -e "$HOME/.local/bin/neo-control-center" ]]; then
    cp -a "$HOME/.local/bin/neo-control-center" "$center_state/backup/launcher"
  fi
  if [[ -e "$HOME/.config/systemd/user/neo-control-center.service" ]]; then
    cp -a "$HOME/.config/systemd/user/neo-control-center.service" "$center_state/backup/control-center-service"
  fi
fi

"$center_python/bin/python3" - "$HOME" "$center_state" <<'PY'
import json
from pathlib import Path
import sys

home, state = map(Path, sys.argv[1:])
config = json.loads((home / ".config/waybar/config").read_text())
bars = config if isinstance(config, list) else [config]
for bar in bars:
    if "custom/control" in bar:
        bar["custom/control"]["on-click-release"] = str(home / ".local/bin/neo-control-center")
    if "image#control" in bar:
        bar["image#control"]["on-click"] = str(home / ".local/bin/neo-control-center")
        # Waybar 0.15 defaults image refresh to 1ms. This icon is static.
        # A finite interval also avoids its "once" duration overflow.
        bar["image#control"]["interval"] = 3600
target = state / "waybar-config.json"
temporary = target.with_suffix(".tmp")
temporary.write_text(json.dumps(config, indent=2) + "\n")
temporary.replace(target)
PY

ln -sfn "$(readlink -f "$center_state/package")/bin/neo-control-center" \
  "$HOME/.local/bin/neo-control-center"
ln -sfn "$center_state/waybar-config.json" "$HOME/.config/waybar/config"
if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
  # Replace the old snapshot renderer and preload the native panel hidden.
  systemctl --user stop neo-pyglass-fast-check.service neo-control-center.service 2>/dev/null || true
  pkill -u "$UID" -TERM -f '^/nix/store/[^ ]*-python3[^ ]*/bin/python3 /nix/store/[^ ]*-neo-control-center-[^ ]*/share/neo-control-center/main.py' || true
  mkdir -p "$HOME/.config/systemd/user"
  ln -sfn "$(readlink -f "$center_state/package")/share/systemd/user/neo-control-center.service" \
    "$HOME/.config/systemd/user/neo-control-center.service"
  systemctl --user import-environment WAYLAND_DISPLAY DISPLAY XDG_RUNTIME_DIR HYPRLAND_INSTANCE_SIGNATURE
  systemctl --user daemon-reload
  systemctl --user enable --now neo-control-center.service
  # Waybar's reset signal can retain cached actions. Restart only the bar.
  systemctl --user stop neo-waybar-pyglass.service 2>/dev/null || true
  if systemctl --user is-active --quiet neo-waybar-control-center.service; then
    systemctl --user restart neo-waybar-control-center.service
  else
    pkill -u "$UID" -TERM -x 'waybar|\.waybar-wrapped' || true
    systemd-run --user --unit=neo-waybar-control-center --collect \
      --setenv="WAYLAND_DISPLAY=$WAYLAND_DISPLAY" \
      --setenv="DISPLAY=${DISPLAY:-}" --setenv="XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR" \
      "$(command -v waybar)" -c "$HOME/.config/waybar/config" \
      -s "$HOME/.config/waybar/style.css"
  fi
fi
printf '%s\n' 'Native Control Center activated. Open it with the two-switch button in Waybar.'
printf 'Previous configuration saved in %s/backup\n' "$center_state"
