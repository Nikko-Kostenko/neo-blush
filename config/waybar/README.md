# Neo Blush Waybar

A transparent macOS Liquid Glass-style menu bar with SF Pro typography,
locally installed Apple symbol glyphs, and pink glass menus. The Apple menu,
active application's name, application launcher and four Hyprland workspace
marks sit on the left. Battery, Wi-Fi, Bluetooth, other tray items, search,
Control Center and the clock sit on the right. Audio and brightness remain in
Control Center. NetworkManager's tray item uses the locally exported SF Wi-Fi
symbol and opens its live network list directly below the icon. Bluetooth uses
a matching monochrome drawing and opens Blueman's device menu on left-click.
Offline, wired and disabled states have corresponding icon variants. Other
third-party tray applications retain their own icons.
The layout follows [Apple's transparent menu bar design](https://www.apple.com/uk/newsroom/2025/06/macos-tahoe-26-makes-the-mac-more-capable-productive-and-intelligent-than-ever/).

Menu text is 14 px and the Apple logo is 24 px. The centered Dynamic Island is
a native Waybar custom module, with a dark capsule and pink SF symbols. It
stays compact when idle, expands for playing or paused media, and shows volume
and brightness changes for three seconds before returning to playback or idle.
Click it to play/pause the selected player; when idle, clicking opens Control
Center. Right-click always opens Control Center, and scrolling adjusts volume.
MPRIS D-Bus signals supply live media updates and a single `pactl subscribe`
process supplies audio events. Brightness reads two small sysfs files once a
second because backlight file-change notifications are unreliable. There is
no media polling, screen capture, PyGlass or separate graphical window.
Waybar owns the helper and stops it on exit.

All GTK dropdowns, including tray menus and submenus, share Control Center's
three-stop pink glass gradient, light rim and soft inset shadows. Dropdown
rows use 13 px SF Pro text, rounded hover highlights and explicit dark rose
foregrounds; disabled entries remain muted. Hover tooltips and the clock's
calendar use the same material, with readable dark text rather than GTK's
default selected foreground. Workspace dots retain their state colours.

HyprGlass supplies GPU blur and refraction for Control Center, the menu bar
and Rofi, using the pink Neo Blush preset. GTK dropdowns keep Hyprland's native
popup blur and the matching material: the pinned plugin does not process GTK
popup render passes. GTK
supplies native controls in a floating macOS Liquid Glass layout: separate
Wi-Fi/Bluetooth capsules, a media tile, circular shortcuts and wide sliders.
The layout has no enclosing background, header or border. Each control has
its own translucent pink material, rounded corners and a thin highlight.
The controller remains loaded between openings and stops polling
while hidden. There is no PyGlass, Qt renderer, NumPy or screen capture.
The palette matches the MacBook Neo Blush wallpaper and Kitty theme.

The layout follows [Apple's current Control Center reference](https://support.apple.com/en-in/guide/mac-help/mchl50f94f8f/mac).
The package includes custom SVG drawings as fallbacks. Local Apple symbol
exports in `~/.local/share/neo-control-center/icons` override these drawings;
the panel prefers installed SF Pro Text and SF Pro Display fonts over Inter.
Apple assets stay in the user's local data directory, outside the Nix package.
The controls operate the Linux
desktop's own devices and services. Clicking anywhere on a Wi-Fi/Bluetooth
capsule, including the glyph or name, toggles that radio.
The menu bar's Wi-Fi and Bluetooth icons provide their dropdown options.
The Sound output button opens audio settings.

See [the desktop theme guide](../../NEO-THEME.md) for application, controls,
customization, wallpaper attribution, backups, and rollback.

Click the two-switch symbol beside the clock to open the panel. Click outside it,
press Escape, or click the icon again to close it. It contains:

- Wi-Fi and Bluetooth toggles, connection status, and buttons for their settings.
- Display brightness and speaker volume sliders, plus speaker mute and audio settings.
- The currently playing media's title and artist, with previous, play/pause, and next.
- Microphone mute, Keep Awake, battery status, and screen lock.

Keep Awake continues after the panel closes; switch it off in the panel to allow
idle and sleep again. It resets when the user session ends. Controls without
available hardware or a media player are disabled. Brightness controls laptop
backlights; external monitors need their own DDC controls.

Activate the menu bar without root or a system rebuild:

```sh
bash ./config/waybar/activate-menu-bar.sh
```

It restarts only Waybar and saves its prior configuration and stylesheet in
`~/.local/state/neo-menu-bar/backup`. Install your local SF Pro fonts using the
asset importer below before activating this layout. The Control Center button
uses a static font glyph and opens on mouse release, with no image refresh
thread. Workspace dots remain clickable and reflect Hyprland's active workspace.
The installer builds a small Waybar patch to anchor tray menus below their
icons, support Bluetooth's left-click menu and preserve custom icons when apps
publish status changes. The same patched package is selected by Home Manager.
NetworkManager and Blueman still supply the menus and handle device operations;
there is only one Wi-Fi indicator.

Activate just the native panel without root or a system rebuild:

```sh
bash ./config/waybar/activate-control-center.sh
```

The installer builds the GTK package, runs its checks, installs a user launcher,
preloads the panel hidden and reconnects the existing Waybar button. It restarts
only Waybar. The prior configuration is saved in
`~/.local/state/neo-control-center/backup`; earlier PyGlass backups remain in
`~/.local/state/neo-pyglass/backup`.

Opening and closing signal the resident panel over D-Bus. After the initial
startup, neither operation reloads GTK. Escape and outside clicks hide it
immediately. The visible layer is bounded to the panel and uses on-demand
keyboard focus. Hyprland observes outside mouse releases without consuming
them, so a single click both closes the panel and reaches another window or
the bar. Merely moving the pointer outside does not dismiss it. A panel-only
Escape binding also works when focus follows the pointer to another window.
This keeps HyprGlass from processing the full screen for Control Center.
Alpha masks preserve the gaps between capsules;
refraction geometry follows the panel's overall bounds.

HyprGlass is pinned to v0.6.4 for Hyprland 0.55.4. Its launcher verifies the
compositor ABI before loading. Activate it without a system rebuild using:

```sh
bash ./config/hyprglass/activate.sh
```

The installer preserves the existing Hyprland configuration, backs it up in
`~/.local/state/neo-hyprglass/backup`, and restarts only Control Center.
Use `~/.local/bin/neo-hyprglass off` to restore normal compositor blur, or
`~/.local/bin/neo-hyprglass on` to enable the preset again. The choice persists
across config reloads and service restarts. Ordinary application windows retain
their existing styling. The Home Manager module installs the same integration
for future rebuilds.

Set `NEO_GLASS_REDUCE_TRANSPARENCY=1` in the panel's environment for an opaque
surface. GTK's animation preference controls the short control transitions.
The Control Center's compositor open/close animations are disabled for speed.

The glass uses one blur pass at strength 0.55, a lighter surface fill and a
restrained rim. Active radio glyphs use the pink accent; inactive ones remain
neutral. This adapts Apple's [Liquid Glass guidance](https://developer.apple.com/videos/play/wwdc2025/219/)
for readable controls, selective tint and a single floating control layer.

To import assets from your own SF Symbols installer, extract its
`Library/Fonts` directory and run `control-center/import-apple-assets.py` with
that directory using Python with fontTools installed. It installs four SF Pro
font faces and exports fifteen filled symbol outlines as small GTK symbolic
SVGs. The PUA mapping follows
[SF-Symbols-JSON](https://github.com/qzrzz/SF-Symbols-JSON).
Bluetooth retains the bundled drawing because it is absent from that symbol
catalog. Restart `neo-control-center.service` after importing to load the fonts
and icons. The importer is only used during setup; opening the panel does not
load fontTools or extract assets.

To restore the previous panel after user activation:

```sh
systemctl --user disable --now neo-control-center.service
rm ~/.config/systemd/user/neo-control-center.service
cp -a --remove-destination ~/.local/state/neo-control-center/backup/launcher ~/.local/bin/neo-control-center
cp -a --remove-destination ~/.local/state/neo-control-center/backup/waybar-config ~/.config/waybar/config
systemctl --user daemon-reload
systemctl --user restart neo-waybar-control-center.service
```

If there was an existing `neo-control-center.service`, its original unit is
saved as `backup/control-center-service`; restore and enable it as well.

The Home Manager source includes the same package and launcher for declarative
rebuilds. Run these commands from your own NixOS configuration directory,
replacing `my-pc` with your configured hostname:

```sh
sudo nixos-rebuild test --flake "path:$PWD#my-pc"
hyprctl reload
pkill -USR2 -x 'waybar|\.waybar-wrapped'
```

Check `hyprctl configerrors`, then persist the tested configuration:

```sh
sudo nixos-rebuild switch --flake "path:$PWD#my-pc"
```

Home Manager preloads the hidden panel with a user service at session startup.
The launcher can also start it on demand if the service is unavailable.

Older configurations using the image module need an explicit long refresh
interval: Waybar 0.15 defaults an omitted image interval to one millisecond,
which can flood GTK's event queue and freeze the entire bar. The current layout
uses the static `custom/control` module instead.

`config.json` defines the bar and actions; `style.css` styles the bar and menus.
`custom/control` displays Apple's two-switch glyph from the local SF Pro font.
`control-center/` contains
the GTK panel, theme, desktop command backend, package and
regression checks. `default.nix` integrates it with Home Manager.
`menus/*.xml` contains the other GTK menus.
`menu-bar-package.nix` and `patches/tray-menus.patch` supply the native tray
changes. Activation copies and tints local Wi-Fi symbols into
`~/.local/share/neo-menu-bar/icons` alongside the Bluetooth drawing.
