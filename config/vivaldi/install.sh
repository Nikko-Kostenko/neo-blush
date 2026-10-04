#!/usr/bin/env bash
set -euo pipefail
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
flake_dir=$(cd -- "$source_dir/../.." && pwd)
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/vivaldi-neo"
mkdir -p "$state_dir"

# Assets were exported during preparation. Recreate only if missing.
if [[ ! -f "$HOME/.local/share/vivaldi-neo/icons/provenance.json" ]]; then
  tools_python="$HOME/.local/state/neo-control-center/asset-tools/bin/python3"
  if [[ -x "$tools_python" ]]; then
    "$tools_python" "$source_dir/export-assets.py"
  else
    nix shell "path:$flake_dir#vivaldi-neo-asset-tools" \
      -c python3 "$source_dir/export-assets.py"
  fi
fi

# path: includes this module even while its files are not tracked by Git.
nix build "path:$flake_dir#vivaldi-neo" --out-link "$state_dir/package"
package_dir=$(readlink -f -- "$state_dir/package")
if [[ "$(readlink -f -- "$HOME/.nix-profile/bin/vivaldi-neo" 2>/dev/null || true)" != "$(readlink -f -- "$package_dir/bin/vivaldi-neo")" ]]; then
  if [[ -f "$state_dir/profile-installed" ]]; then
    nix profile upgrade vivaldi-neo
  else
    nix profile install --priority 4 "path:$flake_dir#vivaldi-neo"
    touch "$state_dir/profile-installed"
  fi
fi
"$package_dir/bin/vivaldi-neo-apply" --if-needed
mkdir -p "$HOME/.local/share/applications"
install -m644 -- "$package_dir/share/applications/vivaldi-neo.desktop" "$HOME/.local/share/applications/vivaldi-neo.desktop"
if command -v update-desktop-database >/dev/null; then
  update-desktop-database "$HOME/.local/share/applications"
fi
printf 'Installed Vivaldi Neo Blush. Opening the browser.\n'
exec "$package_dir/bin/vivaldi-neo" "$@"
