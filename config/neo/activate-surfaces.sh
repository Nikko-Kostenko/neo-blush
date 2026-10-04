#!/usr/bin/env bash
# Apply desktop styles without rebuilding NixOS or restarting shells.
set -euo pipefail
surface_repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
surface_config="${XDG_CONFIG_HOME:-$HOME/.config}"
surface_state="${XDG_STATE_HOME:-$HOME/.local/state}/neo-surfaces"
surface_backup="$surface_state/backup/$(date +%Y%m%d-%H%M%S)-$$"

kitty +runpy 'import sys; from kitty.config import load_config; bad=[]; load_config(sys.argv[1], accumulate_bad_lines=bad); print(*bad, sep="\n"); raise SystemExit(bool(bad))' \
  "$surface_repo/config/kitty/kitty.conf"
rofi -config "$surface_repo/config/rofi/config.rasi" -dump-theme >/dev/null

mkdir -p "$surface_backup" "$surface_config"
for surface_app in kitty rofi; do
  surface_live="$surface_config/$surface_app"
  surface_target="$surface_state/$surface_app"
  if [[ ! -d "$surface_target" ]]; then
    mkdir -p "$surface_target"
    if [[ -d "$surface_live" ]]; then
      cp -RL "$surface_live/." "$surface_target/"
      chmod -R u+rwX "$surface_target"
    fi
  fi
  if [[ -e "$surface_live" || -L "$surface_live" ]]; then
    cp -RL "$surface_live" "$surface_backup/$surface_app"
  fi
done
cp "$surface_repo/config/kitty/kitty.conf" "$surface_state/kitty/kitty.conf"
cp "$surface_repo/config/rofi/"*.rasi "$surface_state/rofi/"
for surface_app in kitty rofi; do
  surface_live="$surface_config/$surface_app"
  surface_target="$surface_state/$surface_app"
  if [[ -L "$surface_live" ]]; then
    ln -sfn "$surface_target" "$surface_live"
  elif [[ -e "$surface_live" ]]; then
    mv "$surface_live" "$surface_backup/$surface_app-original"
    ln -s "$surface_target" "$surface_live"
  else
    ln -s "$surface_target" "$surface_live"
  fi
done

# This desktop runs Waybar with a mutable, watched stylesheet.
surface_bar="$surface_config/waybar/style.css"
if [[ -e "$surface_bar" ]]; then
  cp -L "$surface_bar" "$surface_backup/waybar-style.css"
fi
mkdir -p "$surface_config/waybar"
if [[ -f "$surface_bar" && -w "$surface_bar" ]]; then
  cp "$surface_repo/config/waybar/style.css" "$surface_bar"
else
  cp "$surface_repo/config/waybar/style.css" "$surface_state/waybar-style.css"
  ln -sfn "$surface_state/waybar-style.css" "$surface_bar"
fi
if systemctl --user is-active --quiet neo-waybar-control-center.service; then
  systemctl --user restart neo-waybar-control-center.service
fi
while IFS= read -r surface_pid; do
  kill -USR1 "$surface_pid"
done < <(pgrep -u "$UID" -x 'kitty|\.kitty-wrapped' || true)
printf 'Kitty, Rofi and menu styles applied. Backup: %s\n' "$surface_backup"
