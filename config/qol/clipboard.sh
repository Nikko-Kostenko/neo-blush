set -euo pipefail

case "${1:-pick}" in
  pick)
    history=$(cliphist list) || {
      rofi -e 'Clipboard history is unavailable. Copy an item first, or check the clipboard services.'
      exit 1
    }
    if [[ -z "$history" ]]; then
      rofi -e 'Clipboard history is empty. Copy some text or an image first.'
      exit 0
    fi
    selection=$(printf '%s\n' "$history" |
      rofi -dmenu -i -no-custom -p 'Clipboard') || exit 0
    [[ -n "$selection" ]] || exit 0
    printf '%s\n' "$selection" | cliphist decode | wl-copy
    ;;
  clear)
    selection=$(printf 'Cancel\nClear history\n' |
      rofi -dmenu -i -no-custom -p 'Clear clipboard history?') || exit 0
    [[ "$selection" == 'Clear history' ]] || exit 0
    cliphist wipe
    ;;
  *) printf 'Usage: neo-clipboard [pick|clear]\n' >&2; exit 2 ;;
esac
