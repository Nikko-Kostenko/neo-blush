#!/usr/bin/env bash
set -euo pipefail
NEO_FILES_REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
files_state="${XDG_STATE_HOME:-$HOME/.local/state}/neo-files"
mkdir -p "$files_state" "$HOME/.local/bin" "$HOME/.local/share/applications"
nix build "path:$NEO_FILES_REPO#neo-files" \
  --out-link "$files_state/package"
mkdir -p "$HOME/.config/systemd/user" "$HOME/.local/share/dbus-1/services"
ln -sfn "$files_state/package/share/neo-files/xfconfd.service" \
  "$HOME/.config/systemd/user/xfconfd.service"
ln -sfn "$files_state/package/share/neo-files/org.xfce.Xfconf.service" \
  "$HOME/.local/share/dbus-1/services/org.xfce.Xfconf.service"
ln -sfn "$files_state/package/share/neo-files/tumblerd.service" \
  "$HOME/.config/systemd/user/tumblerd.service"
for files_service in "$files_state/package/share/neo-files"/org.xfce.Tumbler.*.service; do
  ln -sfn "$files_service" "$HOME/.local/share/dbus-1/services/$(basename "$files_service")"
done
if [[ -L "$HOME/.local/share/dbus-1/services/org.xfce.Tumbler.service" && ! -e "$HOME/.local/share/dbus-1/services/org.xfce.Tumbler.service" ]]; then
  rm "$HOME/.local/share/dbus-1/services/org.xfce.Tumbler.service"
fi
systemctl --user daemon-reload
busctl --user call org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus ReloadConfig
systemctl --user start xfconfd.service
"$files_state/package/bin/neo-files-configure" "$NEO_FILES_REPO"
ln -sfn "$files_state/package/bin/neo-files" "$HOME/.local/bin/neo-files"
ln -sfn "$files_state/package/share/applications/thunar.desktop" \
  "$HOME/.local/share/applications/thunar.desktop"
if [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
  hyprctl reload
fi
if systemctl --user is-active --quiet neo-waybar-control-center.service; then
  systemctl --user restart neo-waybar-control-center.service
fi
printf '%s\n' 'Thunar styling and file-manager launch routes applied.'
