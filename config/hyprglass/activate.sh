#!/usr/bin/env bash
# Activate the pinned plugin and bounded native panel as the desktop user.
set -euo pipefail
NEO_THEME_REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
glass_state="${XDG_STATE_HOME:-$HOME/.local/state}/neo-hyprglass"
mkdir -p "$glass_state/backup"
nix build "path:$NEO_THEME_REPO#neo-hyprglass" \
  --out-link "$glass_state/launcher"
nix build "path:$NEO_THEME_REPO#neo-control-center" \
  --out-link "$glass_state/control-center"
"$glass_state/launcher/bin/neo-hyprglass" check
"$glass_state/control-center/bin/neo-control-center" --self-test

# Preserve the current installed config, including local edits outside this repo.
if [[ ! -e "$glass_state/backup/hypr" ]]; then
  cp -a "$HOME/.config/hypr" "$glass_state/backup/hypr"
fi
for glass_file in "$HOME/.local/bin/neo-control-center" \
                  "$HOME/.config/systemd/user/neo-control-center.service"; do
  backup_name=$(basename "$glass_file")
  if [[ -e "$glass_file" && ! -e "$glass_state/backup/$backup_name" ]]; then
    cp -a "$glass_file" "$glass_state/backup/$backup_name"
  fi
done
if [[ "$(readlink -f "$HOME/.config/hypr")" != "$glass_state/hypr" ]]; then
  mkdir -p "$glass_state/hypr"
  cp -aL "$HOME/.config/hypr/." "$glass_state/hypr/"
  chmod -R u+w "$glass_state/hypr"
fi
cp "$NEO_THEME_REPO/config/hypr/hyprglass.lua" "$glass_state/hypr/hyprglass.lua"
# Retain the native tray fixes on login before the next Home Manager rebuild.
# That rebuild selects the same patched Waybar through programs.waybar.package.
patched_bar="${XDG_STATE_HOME:-$HOME/.local/state}/neo-menu-bar/waybar/bin/waybar"
if [[ -x "$patched_bar" ]]; then
  sed -i 's|hl.exec_cmd("waybar")|hl.exec_cmd((os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")) .. "/neo-menu-bar/waybar/bin/waybar")|' \
    "$glass_state/hypr/hyprland.lua"
fi
if ! rg -q '^require\("hyprglass"\)' "$glass_state/hypr/hyprland.lua"; then
  printf '\n-- Optional Neo Blush HyprGlass integration.\nrequire("hyprglass")\n' \
    >> "$glass_state/hypr/hyprland.lua"
fi
if [[ -d "$HOME/.config/hypr" && ! -L "$HOME/.config/hypr" ]]; then
  mv "$HOME/.config/hypr" "$glass_state/hypr-before-$(date +%s)"
fi
ln -sfn "$glass_state/hypr" "$HOME/.config/hypr"
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/neo-hyprglass" \
         "$HOME/.config/systemd/user/neo-control-center.service.d"
ln -sfn "$(readlink -f "$glass_state/launcher")/bin/neo-hyprglass" \
  "$HOME/.local/bin/neo-hyprglass"
ln -sfn "$NEO_THEME_REPO/config/hyprglass/preset.lua" \
  "$HOME/.local/share/neo-hyprglass/preset.lua"
ln -sfn "$(readlink -f "$glass_state/control-center")/bin/neo-control-center" \
  "$HOME/.local/bin/neo-control-center"
ln -sfn "$(readlink -f "$glass_state/control-center")/share/systemd/user/neo-control-center.service" \
  "$HOME/.config/systemd/user/neo-control-center.service"
cat > "$HOME/.config/systemd/user/neo-control-center.service.d/hyprglass.conf" <<EOF
[Service]
ExecStartPost=-$HOME/.local/bin/neo-hyprglass apply
EOF
systemctl --user import-environment WAYLAND_DISPLAY DISPLAY XDG_RUNTIME_DIR HYPRLAND_INSTANCE_SIGNATURE
systemctl --user daemon-reload
# Load first; config reload then commits presets/masks through hyprglass.lua.
"$HOME/.local/bin/neo-hyprglass" on
systemctl --user restart neo-control-center.service
printf 'HyprGlass activated. Backups: %s/backup\n' "$glass_state"
