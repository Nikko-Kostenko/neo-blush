# Download Apple's original MacBook Neo Blush wallpaper once, then reuse it.
set -euo pipefail

wallpaper_dir="$HOME/.local/share/wallpapers"
wallpaper_path="$wallpaper_dir/macbook-neo-blush.jpg"
wallpaper_url="https://media.idownloadblog.com/wp-content/uploads/2026/03/MacBook-Neo-wallpaper-Pink.jpeg"

is_jpeg() {
    [[ -s "$1" ]] && [[ "$(od -An -tx1 -N3 "$1" | tr -d ' \n')" == "ffd8ff" ]]
}

if ! is_jpeg "$wallpaper_path"; then
    mkdir -p "$wallpaper_dir"
    download_path=$(mktemp "$wallpaper_dir/.neo-download.XXXXXX")
    trap 'rm -f "$download_path"' EXIT
    curl --fail --location --proto '=https' --tlsv1.2 \
        --connect-timeout 10 --max-time 120 --retry 2 \
        --output "$download_path" "$wallpaper_url"
    if ! is_jpeg "$download_path"; then
        printf '%s\n' 'The wallpaper download is not a JPEG; keeping the previous file.' >&2
        exit 1
    fi
    chmod 644 "$download_path"
    mv "$download_path" "$wallpaper_path"
    trap - EXIT
fi

if [[ "${1:-}" != "--download-only" ]]; then
    exec hyprpaper
fi
