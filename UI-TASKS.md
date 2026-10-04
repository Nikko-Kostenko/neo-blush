# Neo Blush UI tasks

Make the desktop feel closer to macOS while retaining the pink palette,
Hyprland workspace marks, working Linux controls, and fast native rendering.
Glass on Linux is an approximation; compare layout and behavior against a
specific macOS reference before claiming a visual match.

## Already applied

- [x] Native Control Center with floating glass elements and whole-button
  Wi-Fi/Bluetooth toggles.
- [x] Transparent menu bar with SF Pro, local Apple symbols where available,
  workspace marks, and Dynamic Island.
- [x] Matching pink glass styling for menu dropdowns, Kitty, and Rofi.
- [x] Finder-inspired Dolphin theme with SF typography and local symbols,
  an opaque file area, and an individual HyprGlass preset for translucent chrome.
- [x] Replace the default with Thunar for more direct GTK styling: rounded pink
  selections, softer file-area edges, local SF icons, and HyprGlass navigation.
  Keep Dolphin available as a fallback.

These are the starting point. The checks below still need to be completed.

## Priority 1 — consistent design and reliable interactions

- [ ] Choose a macOS reference for the menu bar, Control Center, Spotlight,
  and menus. Record screenshots and check Apple's current design guidance.
  Compare proportions, spacing, typography, and states against that reference.
- [ ] Define shared colors, type sizes, spacing, radii, borders, and shadows.
  Give floating controls, dense menus, and terminal content appropriate tint
  levels while keeping one visual language.
- [ ] Audit every menu bar icon for optical size, baseline, weight, and click
  area. Use verified local SF assets; identify fallbacks when originals are absent.
- [ ] Standardize menu placement, row heights, separators, disabled text, and
  hover highlights. Verify Wi-Fi and Bluetooth dropdowns open under their icons
  on the intended mouse button and dismiss consistently.
- [ ] Recheck Control Center opening, closing, outside clicks, Escape, radio
  toggles, and busy states. Outside clicks must reach the underlying application;
  moving the pointer outside must keep the panel open.
- [ ] Measure panel and launcher opening time, animation smoothness, and idle
  CPU use. Keep asset extraction out of opening paths and stop unnecessary
  polling while panels are hidden. Record results before and after changes.

## Priority 2 — refine the main desktop surfaces

- [ ] Refine Control Center geometry: capsule proportions, slider tracks,
  icon/text alignment, media controls, and active/off states.
- [ ] Refine the menu bar: application names, consistent status spacing,
  date/time formatting, and hover feedback. Keep workspace marks visible.
- [ ] Improve Dynamic Island transitions and truncation. Keep it centered
  as content changes; verify media actions and volume/brightness feedback.
- [ ] Refine Rofi toward the chosen Spotlight reference: search field,
  result spacing, selection, application icons, and keyboard navigation.
  Keep session prompts and confirmation messages visible.
- [ ] Polish Kitty tabs, padding, cursor, selection, and ANSI contrast.
  Preserve monospaced terminal columns and working native tab controls.
- [x] Give notifications the same typography, spacing, and material.
  Verify actions, dismissal, long text, and Do Not Disturb behavior.

## Priority 3 — extend the theme and verify the whole experience

- [ ] Align GTK and Qt application controls, dialogs, tooltips, and file
  pickers with the desktop palette. Check the actual applications in use.
  Use HyprGlass where the toolkit provides suitable translucency, with a native
  blur fallback and a check of performance and text contrast.
- [ ] Refine the file manager and browser chrome: toolbar density, tabs,
  sidebar selection, and icons, while preserving their existing functionality.
- [ ] Audit login and lock screens for consistent fonts, identity layout,
  password focus, error messages, and readable contrast.
- [ ] Tune window borders, shadows, corners, and short open/close animations.
  Check both tiled and floating windows; provide reduced-motion settings.
- [ ] Provide a readable reduced-transparency appearance. Check bright and
  dark backdrops, keyboard focus, long labels, and different display scales.
- [ ] Verify saved configuration matches the running desktop and survives
  a Home Manager rebuild and a later login. Document activation and rollback.

## Completion criteria

For each surface: inspect its normal, hovered, selected, disabled, and expanded
states where applicable; verify mouse and keyboard interactions; check runtime
logs; and record a screenshot. Mark a task complete only after activation and
the relevant checks pass.

## Source locations

| Surface | Source |
| --- | --- |
| Menu bar and dropdowns | `config/waybar/style.css`, `config/waybar/config.json`, `config/waybar/menus/` |
| Control Center | `config/waybar/control-center/` |
| Dynamic Island | `config/waybar/dynamic-island/` |
| Rofi | `config/rofi/` |
| Kitty | `config/kitty/kitty.conf` |
| Files (Thunar) | `config/files/` |
| Dolphin fallback | `config/dolphin/` |
| Compositor and lock screen | `config/hypr/` |
| Glass effects | `config/hyprglass/` |
| Login screen | `sddm/neo-glass/` |

See [NEO-THEME.md](NEO-THEME.md) for activation and existing controls.
