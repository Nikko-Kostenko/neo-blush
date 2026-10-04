# Neo Blush SDDM

A Qt 6 login screen with the Neo Blush wallpaper, a date and clock, Wi-Fi and
battery indicators, a circular account image or initial, and a compact password
field. User and session choices come from SDDM. Wi-Fi and battery indicators
appear when the corresponding hardware is available.

Import `neo.nixosModules.default` to install the theme with the desktop. The
module loads the theme from its versioned Nix store path and applies it on the
next display-manager start. The wallpaper is bundled and works offline.

## Customize

Set `neo.sddm.avatar = ./avatar.jpg;` and `neo.sddm.avatarUser = "alice";` in your
own NixOS configuration for a login photo. Defaults use the account's initial.

The QML files in `theme/` control the layout, menus, buttons, and pink glass
appearance. `theme/theme.conf` supplies the wallpaper, accent, and font settings.
The `NeoStatus` plugin in `status/` reads NetworkManager over the system bus and
battery state from `/sys/class/power_supply`. It does not change network settings.

Escape clears and hides the password field. Failed authentication allows a
retry, and switching users clears the password. Restart and shutdown require
confirmation.

## Validation

The theme build runs `qmllint` and Qt Quick tests for login interactions,
wallpaper and photo rendering, the initial fallback, status visibility,
user/session selection, authentication retries, and power confirmation.
Tests use synthetic Alice and Guest accounts.

After rebuilding, preview the theme without real login or power actions:

```bash
sddm-greeter-qt6 --test-mode --theme /run/current-system/sw/share/sddm/themes/neo-glass
```

Wallpaper source: [iDownloadBlog's original MacBook Neo wallpapers](https://www.idownloadblog.com/2026/03/11/macbook-neo-wallpapers/).
Implementation references: [SDDM theming](https://github.com/sddm/sddm/blob/develop/docs/THEMING.md),
[Qt MultiEffect](https://doc.qt.io/qt-6/qml-qtquick-effects-multieffect.html), and
[QML disk caching](https://doc.qt.io/qt-6/qmldiskcache.html).
