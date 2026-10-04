# Brave Neo Blush

Use Brave's native light color theme with a neutral blush seed, compact horizontal
tabs, rounded web content, tab previews and a subtle app menu icon. Hide the
Rewards, Wallet, Leo and side-panel toolbar buttons, plus the New Tab stats,
news, clock and promotional widgets. Their services remain available in menus.
The browser keeps its native navigation, Shields and window controls.

This is a macOS-inspired appearance within Brave's existing interface. Brave's
theme preferences do not move the address field, add macOS window decorations,
or provide Apple's Liquid Glass. The existing Hyprland desktop supplies the
outer window corners and shadows.

The Home Manager module packages `brave-neo-apply` and `brave-neo`, supplies both
Brave desktop entries and applies the preset once on activation. It defers if
Brave is open, and later launches and rebuilds preserve changes you make in Brave.
Appearance preferences are merged, with private backups saved before changes.

Rebuild from your own NixOS configuration directory, replacing `my-pc` with
your configured hostname:

```sh
sudo nixos-rebuild switch --flake "path:$PWD#my-pc"
```

To reapply, quit Brave completely and run `brave-neo-apply` from your PATH
after rebuilding.
To undo, quit Brave and run `brave-neo-apply --undo BACKUP_DIRECTORY`, using the
directory recorded in `~/.local/state/brave-neo/Default-applied.json`.
Undo restores only appearance keys, preserving subsequent browsing settings,
and marks setup as handled so later launches do not reapply the preset.
Full private backups also live under `~/.local/state/brave-neo/backups/`.

Implementation references:

- [Brave appearance settings](https://brave.com/whats-new/customize-appearance/)
- [Chromium theme preferences](https://github.com/chromium/chromium/blob/main/chrome/common/pref_names.h)
- [Chromium theme initialization](https://github.com/chromium/chromium/blob/main/chrome/browser/themes/theme_service.cc)
- [Brave tab preferences](https://github.com/brave/brave-core/blob/master/browser/ui/tabs/brave_tab_prefs.h)
