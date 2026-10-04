#!/usr/bin/env bash
set -euo pipefail
: "${NEO_HYPRGLASS_PACKAGE:?Packaged plugin path required}"
: "${NEO_HYPRGLASS_PRESET:?Packaged preset path required}"
glass_state="${XDG_STATE_HOME:-$HOME/.local/state}/neo-hyprglass"
mkdir -p "$glass_state"
case "${1:-apply}" in
  off)
    touch "$glass_state/disabled"
    hyprctl eval 'if hl.plugin.hyprglass then hl.plugin.hyprglass.config({ enabled = false, layers = { enabled = false } }) end; if neoHyprglassLayerRule then neoHyprglassLayerRule:set_enabled(false) end; for _, rule in ipairs(neoHyprglassFileRules or {}) do rule:set_enabled(false) end; for _, rule in ipairs(neoHyprglassDolphinRules or {}) do rule:set_enabled(false) end'
    hyprctl reload
    printf '%s\n' 'HyprGlass disabled; normal compositor blur restored.'
    exit 0
    ;;
  on) rm -f "$glass_state/disabled" ;;
  apply) [[ ! -e "$glass_state/disabled" ]] || exit 0 ;;
  check) ;;
  *) printf '%s\n' 'Usage: neo-hyprglass [apply|on|off|check]' >&2; exit 2 ;;
esac
compiled_abi=$(jq -r '.abiHash' "$NEO_HYPRGLASS_PACKAGE/share/neo-hyprglass/compositor.json")
running_abi=$(hyprctl -j version | jq -r '.abiHash')
if [[ "$compiled_abi" != "$running_abi" ]]; then
  printf 'HyprGlass ABI mismatch. Built: %s; running: %s. Rebuild the plugin for this compositor.\n' \
    "$compiled_abi" "$running_abi" >&2
  exit 1
fi
if [[ "${1:-apply}" == check ]]; then
  printf 'HyprGlass matches the running compositor: %s\n' "$running_abi"
  exit 0
fi
if ! hyprctl -j plugin list | jq -e 'any(.[]; .name == "hyprglass")' >/dev/null; then
  hyprctl plugin load "$NEO_HYPRGLASS_PACKAGE/lib/hyprglass.so"
fi
# This plugin commits pending presets and namespace masks in config.reloaded.
# The installed hyprglass.lua reads the preset during that reload.
hyprctl reload
printf '%s\n' 'HyprGlass Neo Blush preset applied.'
