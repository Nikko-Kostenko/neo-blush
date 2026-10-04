# Neo Blush

A pink glass desktop based on the MacBook Neo Blush wallpaper. Hyprland supplies
blur, rounded corners, spring animations, pink highlight borders, and soft shadows.
Kitty uses a translucent pale pink background and a dark text palette. Waybar is
a compact macOS-inspired menu bar, with native dropdown menus, and Rofi is styled
like Spotlight. The lock screen uses the same wallpaper and typography.

The prioritized improvement checklist is in [UI-TASKS.md](UI-TASKS.md).

SDDM now uses the matching [Neo Blush Glass login screen](sddm/neo-glass/README.md),
with its wallpaper bundled in the Nix store. After applying, reboot when convenient
to load it. Rebuilding does not restart the running display manager.

## Apply

Follow the starter or existing-flake instructions in [README.md](README.md).
Rebuild your own NixOS configuration and log into Hyprland. Log out and back in
after applying font or cursor changes. SDDM loads its new theme on its next start.

The desktop wallpaper is downloaded on first login to
`~/.local/share/wallpapers/macbook-neo-blush.jpg` and reused on later logins.
The login wallpaper is bundled in the theme and works offline.
Wallpaper source: [iDownloadBlog's original MacBook Neo wallpapers](https://www.idownloadblog.com/2026/03/11/macbook-neo-wallpapers/).

WhiteSur supplies the 24 px cursor. The dynamic-cursors plugin enlarges the
pointer when it is shaken.

## Controls

| Control | Action |
| --- | --- |
| Apple icon | Desktop dropdown: apps, terminal, files, lock, sleep, and session actions |
| Applications / Super+Space / Super+R | Spotlight-style application search |
| Wi-Fi | Dropdown with network settings and Wi-Fi controls |
| Speaker | Dropdown with mute, volume adjustments, and sound settings; scroll adjusts volume |
| Display | Brightness presets; scroll adjusts brightness |
| Control Center | Two-switch icon opens a glass panel with Wi-Fi, Bluetooth, brightness, sound, media, microphone mute, Keep Awake, battery, and lock |
| Clock | Hover for calendar; scroll changes month; click switches date/time format |
| Super+Q | Kitty |
| Super+E | Files (styled Thunar) |
| Super+L | Lock screen |
| Super+M | Session menu |

Restart, shutdown, and logout ask for confirmation. Brightness and battery
modules appear on supported hardware. Existing workspace and window management
shortcuts remain available. Touchpad scrolling follows the macOS direction.

## Files (Thunar)

Thunar is the default file manager. Its app-specific `NeoBlushFiles` GTK theme
uses SF Pro, locally exported SF icons, rounded pink selections, a wider Places
sidebar, and a minimal toolbar. The navigation surfaces expose HyprGlass; the
file area has a quieter translucent surface with softer edges. The theme is
selected by the native launcher and does not replace the desktop's global GTK
theme. Asset export runs during setup, never when opening a file window.

```sh
bash config/files/activate.sh
```

`Super+E`, the Apple menu's Files action, the app launcher, and directory file
associations open this wrapper. Thunar keeps its native tabs, split view, file
operations, and configurable toolbar. Preferences are editable in the app.
Xfconf supplies their persistence through a small D-Bus user service, and
Tumbler provides thumbnail previews. GVfs is already enabled for file-system
integration. Backups are saved under
`~/.local/state/neo-files/backup`. Change the app's material, spacing, and rounding
in `config/files/gtk.css`, then rebuild the wrapper and open a fresh process.

## Dolphin fallback

Dolphin uses the Neo Blush Qt theme adapted from the pinned WhiteSur Kvantum
theme. SF Pro, a simple icon toolbar, a wider Places sidebar, pale pink selections,
and locally exported Apple symbols align it with the desktop. The file area is
opaque for readable filenames; the toolbar and window chrome are translucent.
Tabs, bookmarks, file operations, and navigation use Dolphin's native controls.
Thumbnail previews can replace folder icons according to view settings.

Apply it without a full system rebuild:

```sh
bash config/dolphin/activate.sh
```

The script backs up preferences under `~/.local/state/neo-dolphin/backup`, builds
the Qt launcher, and updates the mutable menu bar and file-manager key binding.
The app launcher also uses the styled Dolphin desktop entry. The Home Manager
module preserves this setup after a rebuild. Fonts, icons, and colors are also
written to `kdeglobals` because Dolphin uses KDE settings for parts of its UI;
other KDE applications may inherit those choices. SF exports stay in your local
icon directory, with Breeze providing icons absent from the local Apple assets.

## Glass materials

Prefer HyprGlass for supported translucent surfaces when it preserves readable
content and responsive input. It worked in this desktop's previous panel setup
and is enabled for Control Center, Waybar, Rofi, Thunar, and the Dolphin fallback.

- Match the plugin to the exact running Hyprland ABI. This setup pins HyprGlass
  0.6.4 for Hyprland 0.55.4; the launcher checks compatibility before loading.
- Enable ordinary application windows individually. The file managers use the restrained
  `neo-files` preset; other applications retain normal compositor rendering.
- Create translucency in the application theme. HyprGlass renders underneath it;
  a quiet file or text area keeps its application-defined opacity. Avoid lowering whole-window opacity,
  which also fades text and icons.
- Start with one blur iteration and modest refraction. Check opening, scrolling,
  menus, typing, and contrast on bright, dark, and busy backgrounds before extending
  the effect to another app.
- Keep native Hyprland blur as the fallback. This pinned plugin does not render
  GTK dropdown popups through its layer glass pass; their native blur and matching
  pink styling are deliberate. SDDM runs separately and cannot use session HyprGlass.

Check compatibility with `~/.local/bin/neo-hyprglass check`. Use `off` to disable
glass and restore native blur, `on` to enable it again, and `apply` after preset
changes. These commands reload configuration without restarting the compositor.
Source: [HyprGlass](https://github.com/hyprnux/hyprglass).

## Adjust

- Window blur, borders, and corners: `config/hypr/hyprland.lua`
- Terminal opacity and colors: `config/kitty/kitty.conf`
- Bar layout and actions: `config/waybar/config.json`
- Bar and dropdown appearance: `config/waybar/style.css`
- Control Center panel and appearance: `config/waybar/control-center/`
- HyprGlass material and compatibility pin: `config/hyprglass/`
- Dropdown labels: `config/waybar/menus/*.xml`
- Launcher: `config/rofi/neo-glass.rasi`
- File manager: `config/files/`
- Dolphin fallback: `config/dolphin/`

Reapply after source edits because Home Manager installs store-backed configs.
For just Kitty, Rofi and menu styling, run
`bash config/neo/activate-surfaces.sh`. It validates the terminal and launcher
configs, saves a backup in `~/.local/state/neo-surfaces/backup`, and applies
user-local copies. Existing Kitty shells stay open; the active menu bar service
restarts to load the stylesheet, and Rofi uses the theme on its next opening.
The flake sources also contain these styles for the next Home Manager rebuild. Rofi uses the
locally installed SF Pro fonts and a verified search symbol; Kitty keeps
JetBrains Mono for terminal columns and uses softer fading tabs.

HyprGlass adds GPU refraction and blur to Control Center, Waybar and Rofi with
the pink Neo Blush preset. It is pinned to v0.6.4 for Hyprland 0.55.4 and checks
the compositor ABI before loading. GTK dropdowns use native popup blur with the
same pink styling. Capsule gaps remain transparent; refraction follows the
overall panel bounds. See [the menu bar guide](config/waybar/README.md) for the
user-only installer and controls. To disable the effect without restarting the
desktop, run `~/.local/bin/neo-hyprglass off`; use `on` to enable it again.

## Backups and rollback

The source files from before this change are saved under
`~/.local/state/neo-theme/backups/before-pink-glass/`. Each application of the
script also backs up the installed desktop files in a timestamped directory.
To revert an applied generation, run `sudo nixos-rebuild switch --rollback`,
then log out and back in. That restores the previous system and Home Manager
generation; it does not revert your editable flake sources.
