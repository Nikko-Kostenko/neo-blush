set -euo pipefail
mode="${1:-screen}"
edit="${2:-}"
if [[ -n "$edit" && "$edit" != "--edit" ]]; then
  printf 'Usage: neo-screenshot [area|screen] [--edit]\n' >&2
  exit 2
fi

case "$mode" in
  area)
    # Escape cancels selection without taking a screenshot.
    geometry=$(slurp) || exit 0
    [[ -n "$geometry" ]] || exit 0
    ;;
  screen) ;;
  *)
    printf 'Usage: neo-screenshot [area|screen] [--edit]\n' >&2
    exit 2
    ;;
esac

umask 077
directory="${XDG_PICTURES_DIR:-$HOME/Pictures}/Screenshots"
mkdir -p "$directory"
file="$directory/Screenshot-$(date +%Y-%m-%d_%H-%M-%S-%N).png"

if [[ "$mode" == area ]]; then
  grim -g "$geometry" "$file"
else
  grim "$file"
fi
printf '%s\n' "$file"
wl-copy --type image/png < "$file"
if [[ "$edit" == "--edit" ]]; then
  exec satty --filename "$file" --output-filename "${file%.png}-edited.png"
fi
notify-send --app-name='Screenshot' --icon="$file" \
  'Screenshot copied' "Saved to $directory" || true
