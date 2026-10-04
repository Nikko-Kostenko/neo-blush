# Neo Blush desktop conveniences

This module adds clipboard history, a themed Notification Center, screenshot
annotation, file viewers, local file transfer, password management, backups,
night colors, audio processing, and a resource monitor.

The desktop modules include these conveniences. Apply them by rebuilding your
own configuration following the root [README](../../README.md), then log into
Hyprland.

| Shortcut | Action |
| --- | --- |
| Super+Shift+V | Search copied text and images with Rofi |
| Super+N | Open/close Notification Center |
| Super+Shift+N | Toggle Do Not Disturb |
| Super+Shift+S | Save and copy a selected screenshot |
| Print | Save and copy the screen |
| Super+Shift+A | Capture an area and annotate it in Satty |

The menu bar bell opens notifications; right-click toggles Do Not Disturb.

## Notification Center

The SwayNC panel floats below the menu bar and sizes to its content instead of
stretching across the screen. It uses a softly tinted surface, plum text, quiet
cards, a compact Do Not Disturb switch, and an explicit empty state. Long lists
scroll within the available monitor height. Critical notifications retain a
distinct red border.

Its 16px outer margins match Hyprland's tiled-window gutter, aligning the top
and right edges with ordinary windows. Layer shell already accounts for the
menu bar's reserved space; the top margin does not add the bar's height again.

Notifications from the same application form a stack. Use Up/Down or Home/End
to navigate, Enter to expand a stack, Delete to dismiss, and Escape to close the
panel. Keys 1–9 invoke available actions; Shift+C clears the list and Shift+D
toggles Do Not Disturb. The matching buttons support mouse use.

Edit `notifications.css` for appearance and `notifications.json` for layout.
The CSS targets SwayNC 0.12's GTK 4 variables so headings, timestamps, buttons,
and grouped notifications inherit legible colors. Adwaita icons supply the
symbolic fallback, including the empty-state bell. Hyprland supplies background
blur; the high-opacity surface also keeps text readable without blur.

## Other desktop conveniences

Clipboard history retains up to 200 items. Run `neo-clipboard clear` to clear it
after confirmation.

Screenshots are saved under `~/Pictures/Screenshots` (or `$XDG_PICTURES_DIR`).
In Satty, Enter or Ctrl+C copies the edited image, saves a separate `-edited.png`,
and exits. Ctrl+S saves without copying; Escape closes the editor. The original
capture is retained.

Idle behavior: dim the backlight after 2.5 minutes, lock after 5 minutes, turn
off displays after 5.5 minutes, and suspend after 30 minutes. Locking also runs
before suspend, including lid-triggered sleep. The Control Center's Keep Awake
inhibitor and application idle inhibitors are respected.

Hyprsunset uses normal colors from 07:00 and 4500 K from 20:00, in the machine's
configured timezone. Edit the profiles in `default.nix` to change those times.

PDFs open in Okular, images in Loupe, and supported archives in Ark. Directory
opening remains assigned to the themed Thunar. Browser startup now uses
`vivaldi-neo`.

LocalSend is installed through the NixOS module in `system.nix`, which opens
TCP and UDP port 53317 for discovery and receiving files. Other apps are managed
through Home Manager. KeePassXC needs a database selected or created in the app;
its browser extension is optional. EasyEffects is available without automatically
applying an audio preset.

Pika Backup is available in the app launcher. Choose its destination and
schedule in the application; no backup job is configured by this module.

## Validation

Evaluate your configuration and rebuild it before logging into the desktop.
Check notification, clipboard, idle, and screenshot behavior on your hardware.
