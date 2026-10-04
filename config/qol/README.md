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
