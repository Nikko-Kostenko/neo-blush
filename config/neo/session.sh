set -euo pipefail

action="${1:-menu}"
if [[ "$action" == "menu" ]]; then
    selection=$(printf '%s\n' 'Lock screen' 'Sleep' 'Log out…' 'Restart…' 'Shut down…' |
        rofi -dmenu -i -no-custom -p 'Session') || exit 0
    case "$selection" in
        'Lock screen') action='lock' ;;
        'Sleep') action='sleep' ;;
        'Log out…') action='logout' ;;
        'Restart…') action='reboot' ;;
        'Shut down…') action='poweroff' ;;
        *) exit 0 ;;
    esac
fi

case "$action" in
    lock) exec hyprlock ;;
    sleep) systemctl suspend; exit 0 ;;
    logout) label='Log out' ;;
    reboot) label='Restart' ;;
    poweroff) label='Shut down' ;;
    *) printf 'Unknown session action: %s\n' "$action" >&2; exit 1 ;;
esac

confirmation=$(printf 'Cancel\n%s\n' "$label" |
    rofi -dmenu -i -no-custom -p "$label?" -mesg 'Save your work before continuing.') || exit 0
[[ "$confirmation" == "$label" ]] || exit 0

case "$action" in
    logout) hyprctl dispatch 'hl.dsp.exit()' ;;
    reboot) systemctl reboot ;;
    poweroff) systemctl poweroff ;;
esac
