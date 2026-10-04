#!/usr/bin/env bash
# User-only activation; running file operations are left alone.
set -euo pipefail
NEO_DOLPHIN_REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
dolphin_state="${XDG_STATE_HOME:-$HOME/.local/state}/neo-dolphin"
mkdir -p "$dolphin_state" "$HOME/.local/bin" "$HOME/.local/share/applications"
nix build "path:$NEO_DOLPHIN_REPO#neo-dolphin" \
  --out-link "$dolphin_state/package"
"$dolphin_state/package/bin/neo-dolphin-configure" "$NEO_DOLPHIN_REPO"
ln -sfn "$dolphin_state/package/bin/neo-dolphin" "$HOME/.local/bin/neo-dolphin"
ln -sfn "$dolphin_state/package/share/applications/org.kde.dolphin.desktop" \
  "$HOME/.local/share/applications/org.kde.dolphin.desktop"
if [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
  hyprctl reload
fi
if systemctl --user is-active --quiet neo-waybar-control-center.service; then
  systemctl --user restart neo-waybar-control-center.service
fi
printf '%s\n' 'Dolphin theme applied. New windows use it through neo-dolphin or the app launcher.'
