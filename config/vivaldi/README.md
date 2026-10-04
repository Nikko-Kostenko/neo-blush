# Vivaldi · Neo Blush

Pink glass browser chrome matching the existing desktop: `#fff3f9` surfaces,
`#452c3b` text, `#a83f74` accent, installed SF Pro Text fonts, and the existing
MacBook Neo Blush wallpaper. Twenty-eight toolbar/panel icons use genuine outlines
from the user's local SF Pro font. Assets and provenance live in
`~/.local/share/vivaldi-neo/icons`, outside this repository.

Run from a normal terminal, with Vivaldi closed:

```bash
bash ./config/vivaldi/install.sh
```

This builds the pinned Nix package, installs it in your user profile, merges the
theme into Vivaldi's Default profile, installs its application launcher, and opens
the browser. No sudo, logout, or full system rebuild is needed. It does not change
the default browser or migrate another browser's data. The Home Manager module is
also imported by `home.nix`, so future system rebuilds retain the setup.
While the new files are untracked, use `--flake "path:$PWD#$(hostname)"`
for a system rebuild, or add this module to Git before using a Git-based flake.

The glass effect approximates Apple's materials inside Vivaldi. It blurs the
browser's own theme background; it does not expose desktop wallpaper through web
pages. SF Pro supplies text; SF Symbols are icons, not a text font.

The package adds `neo-blush.css` to Vivaldi's `window.html` (or `browser.html` on
older versions) in a new Nix derivation. Native Linux menus use an app-specific
GTK palette and SF Pro font configuration, both scoped to Vivaldi.
On Hyprland, the launcher also enables compositor blur for translucent popups in
the session. This makes native menus frosted and keeps underlying text from
showing sharply through them; it also applies to other translucent native popups.
Native browser controls, dragging, and keyboard actions remain in Vivaldi. The
window buttons retain their original positions and actions and receive macOS
traffic-light colors. Private windows retain their distinct native colors.
Reduced-motion, reduced-transparency, and missing-blur fallbacks are provided.

`apply.py` checks the installed `prefs_definitions.json` before setting appearance
keys. It refuses to edit locked or uncleanly closed profiles. It backs up profile
preferences with private permissions, preserves existing user themes, and applies
the initial appearance once so later browser settings are not reset at launch.
The native theme can be edited under Settings → Themes. If your installed version
uses a theme schedule that overrides it, select No Scheduling.

Reapply after editing `theme.json` (close Vivaldi first):

```bash
vivaldi-neo-apply
```

For CSS changes, rerun `install.sh` to build the new package. Do not edit `/nix/store`.
The local native theme archive is
`~/.local/state/vivaldi-neo/Neo-Blush-Liquid-Glass.zip`; it can be imported through
Settings → Themes. It contains Apple assets and is intended for personal use.

Undo appearance preferences using the backup path printed by the apply command:

```bash
vivaldi-neo-apply --undo ~/.local/state/vivaldi-neo/backups/BACKUP_DIRECTORY
```

Undo preserves themes added later and appearance settings subsequently changed by
the user. The packaged CSS remains until the normal Vivaldi package is installed
instead. Remove `./config/vivaldi` from the Home Manager imports when reverting the
declarative package.

Vivaldi 8.2.4133.52 was installed and activated on October 3, 2026. The running UI
was checked for the Neo Blush colors, SF Pro typography, loaded SF icon assets,
rounded address field, native panel rendering, and menu opening/Escape dismissal.
Appearance backups and the local theme archive remain in the state directory.
