"""Install the user theme and merge visual preferences without losing tabs."""
import configparser
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

assets = Path(sys.argv[1])
home = Path.home()
config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
data = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
state = Path(os.environ.get("XDG_STATE_HOME", home / ".local/state"))
backup = state / "neo-dolphin/backup" / (datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{os.getpid()}")
backup.mkdir(parents=True)

def save_previous(path):
    if path.exists():
        relative = path.relative_to(config)
        dest = backup / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(path, dest)
        else:
            shutil.copy2(path, dest)

def merge(path, sections):
    save_previous(path)
    ini = configparser.ConfigParser(interpolation=None, strict=False, delimiters=("=",))
    ini.optionxform = str
    if path.exists():
        ini.read(path)
    for section, values in sections.items():
        if not ini.has_section(section):
            ini.add_section(section)
        for key, value in values.items():
            ini[section][key] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        path.unlink()
    with path.open("w") as output:
        ini.write(output, space_around_delimiters=False)

qt = configparser.ConfigParser(interpolation=None)
qt.optionxform = str
qt.read(assets / "qt6ct.conf")
palette_path = config / "qt6ct/colors/neo-blush.conf"
qss_path = config / "qt6ct/qss/neo-dolphin.qss"
for path in (palette_path, qss_path):
    save_previous(path)
    path.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(assets / "neo-dolphin.qss", qss_path)
# Qt's ordered QPalette roles, including the Qt 6 Accent role.
colors = ["#452c3b", "#fff3f9", "#ffffff", "#f2dfea", "#d9b7cc", "#e5cfdd",
          "#452c3b", "#b03957", "#452c3b", "#fff8fc", "#fff3f9", "#452c3b",
          "#edd0e0", "#452c3b", "#a83f74", "#994882", "#faf0f6", "#fff3f9",
          "#fff3f9", "#452c3b", "#76636f", "#a83f74"]
groups = {}
for group, text in (("active", "#452c3b"), ("inactive", "#65535f"), ("disabled", "#9c8895")):
    values = colors.copy()
    for role in (0, 6, 8, 13, 19):
        values[role] = text
    groups[f"{group}_colors"] = ", ".join("#ff" + value[1:] for value in values)
palette = configparser.ConfigParser(interpolation=None)
palette["ColorScheme"] = groups
with palette_path.open("w") as output:
    palette.write(output, space_around_delimiters=False)
qt["Appearance"]["color_scheme_path"] = str(palette_path)
qt["Interface"]["stylesheets"] = str(qss_path)
merge(config / "qt6ct/qt6ct.conf", {s: dict(qt[s]) for s in qt.sections()})
merge(config / "Kvantum/kvantum.kvconfig", {"General": {"theme": "NeoBlushDolphin"}})
merge(config / "kdeglobals", {
    "General": {
        "font": "SF Pro Text,13,-1,5,50,0,0,0,0,0",
        "menuFont": "SF Pro Text,13,-1,5,50,0,0,0,0,0",
        "toolBarFont": "SF Pro Text,13,-1,5,50,0,0,0,0,0",
        "smallestReadableFont": "SF Pro Text,11,-1,5,50,0,0,0,0,0",
        "fixed": "JetBrainsMono Nerd Font,12,-1,5,50,0,0,0,0,0",
    },
    "Icons": {"Theme": "NeoBlush-Dolphin"},
    "KDE": {"SingleClick": "false"},
    "Colors:Window": {"BackgroundNormal": "255,243,249", "ForegroundNormal": "69,44,59", "ForegroundInactive": "118,99,111"},
    "Colors:View": {"BackgroundNormal": "255,248,252", "BackgroundAlternate": "250,240,246", "ForegroundNormal": "69,44,59", "ForegroundInactive": "118,99,111"},
    "Colors:Selection": {"BackgroundNormal": "237,208,224", "ForegroundNormal": "69,44,59", "ForegroundInactive": "118,99,111"},
    "Colors:Button": {"BackgroundNormal": "255,243,249", "ForegroundNormal": "69,44,59"},
    "Colors:Tooltip": {"BackgroundNormal": "255,243,249", "ForegroundNormal": "69,44,59"},
})
theme = config / "Kvantum/NeoBlushDolphin"
save_previous(theme)
if theme.is_symlink():
    theme.unlink()
theme.mkdir(parents=True, exist_ok=True)
theme.chmod(theme.stat().st_mode | 0o700)
for source in (assets / "NeoBlushDolphin").iterdir():
    dest = theme / source.name
    if dest.exists() or dest.is_symlink():
        dest.unlink()
    shutil.copyfile(source, dest)

merge(config / "dolphinrc", {
    "General": {"ShowSelectionToggle": "false", "ShowZoomSlider": "false", "LockPanels": "true", "ShowToolTips": "false"},
    "MainWindow": {"MenuBar": "Disabled"},
    "MainWindow][Toolbar mainToolBar": {"ToolButtonStyle": "IconOnly", "IconSize": "20"},
    "IconsMode": {"IconSize": "48", "PreviewSize": "64", "UseSystemFont": "true", "MaximumTextLines": "2"},
    "DetailsMode": {"IconSize": "22", "UseSystemFont": "true"},
    "PlacesPanel": {"IconSize": "20"},
    "KFileDialog Settings": {"Places Icons Auto-resize": "false", "Places Icons Static Size": "20"},
})
toolbar = data / "kxmlgui5/dolphin/dolphinui.rc"
toolbar.parent.mkdir(parents=True, exist_ok=True)
if toolbar.exists():
    shutil.copy2(toolbar, backup / "dolphinui.rc")
if toolbar.exists() or toolbar.is_symlink():
    toolbar.unlink()
shutil.copyfile(assets / "dolphinui.rc", toolbar)

icons = data / "icons/NeoBlush-Dolphin"
(icons / "scalable/actions").mkdir(parents=True, exist_ok=True)
(icons / "scalable/places").mkdir(parents=True, exist_ok=True)
(icons / "index.theme").write_text('''[Icon Theme]
Name=Neo Blush Dolphin
Comment=Local SF outlines with Breeze fallbacks
Inherits=breeze,hicolor
Directories=scalable/actions,scalable/places

[scalable/actions]
Size=24
MinSize=16
MaxSize=64
Type=Scalable
Context=Actions

[scalable/places]
Size=48
MinSize=16
MaxSize=128
Type=Scalable
Context=Places
''')
# Original outlines are rendered once during setup, kept outside the Nix store.
font_path = data / "fonts/neo-control-center-apple/SF-Pro-Text-Regular.otf"
mapping_path = state / "neo-control-center/apple-assets/symbol-map.json"
symbols = {
    "actions/go-previous": "chevron.left", "actions/go-next": "chevron.right",
    "actions/edit-find": "magnifyingglass", "actions/view-list-details": "list.bullet",
    "actions/view-list-icons": "square.grid.2x2", "actions/application-menu": "ellipsis.circle",
    "places/user-home": "house", "places/user-trash": "trash",
    "places/folder": "folder.fill", "places/folder-download": "arrow.down.circle",
    "places/folder-blue": "folder.fill", "places/inode-directory": "folder.fill",
    "places/user-desktop": "desktopcomputer", "places/folder-pictures": "photo",
    "places/folder-music": "music.note", "places/folder-videos": "film",
    "places/folder-documents": "doc.text", "places/drive-harddisk": "externaldrive",
}
manifest = {}
if font_path.exists() and mapping_path.exists():
    mapping = json.loads(mapping_path.read_text())
    font = TTFont(font_path)
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    for target, symbol in symbols.items():
        value = mapping.get(symbol)
        if value is None:
            continue
        cp = ord(value) if isinstance(value, str) and len(value) == 1 else int(value, 0) if isinstance(value, str) else value
        if cp not in cmap:
            continue
        glyph = glyphs[cmap[cp]]
        bounds = BoundsPen(glyphs)
        glyph.draw(bounds)
        if not bounds.bounds:
            continue
        x0, y0, x1, y1 = bounds.bounds
        extent = 20
        scale = extent / max(x1-x0, y1-y0)
        tx, ty = 12-scale*(x0+x1)/2, 12+scale*(y0+y1)/2
        pen = SVGPathPen(glyphs)
        glyph.draw(pen)
        color = "#bd779e" if symbol == "folder.fill" else "#65535f"
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
               f'<path fill="{color}" transform="matrix({scale} 0 0 {-scale} {tx} {ty})" '
               f'd="{pen.getCommands()}"/></svg>\n')
        (icons / "scalable" / f"{target}.svg").write_text(svg)
        manifest[target] = {"symbol": symbol, "codepoint": f"U+{cp:X}", "glyph": cmap[cp], "font": str(font_path)}
    font.close()
(icons / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
if len(sys.argv) > 2:
    # Update only mutable runtime files; declarative modules cover rebuilds.
    runtime_hypr = config / "hypr/hyprland.lua"
    if runtime_hypr.exists() and os.access(runtime_hypr, os.W_OK):
        old = runtime_hypr.read_text()
        new = re.sub(r'^local fileManager\s*=.*$',
                     'local fileManager = os.getenv("HOME") .. "/.local/bin/neo-dolphin"',
                     old, flags=re.MULTILINE)
        if new != old:
            save_previous(runtime_hypr)
            runtime_hypr.resolve().write_text(new)
    runtime_bar = config / "waybar/config"
    if runtime_bar.exists() and os.access(runtime_bar, os.W_OK):
        bar = json.loads(runtime_bar.read_text())
        bars = bar if isinstance(bar, list) else [bar]
        changed = False
        for entry in bars:
            actions = entry.get("custom/desktop", {}).get("menu-actions", {})
            command = str(home / ".local/bin/neo-dolphin")
            if "files" in actions and actions["files"] != command:
                actions["files"] = command
                changed = True
        if changed:
            save_previous(runtime_bar)
            runtime_bar.resolve().write_text(json.dumps(bar, ensure_ascii=False, indent=2) + "\n")
print(f"Dolphin style configured; {len(manifest)} local Apple symbols. Backup: {backup}")
