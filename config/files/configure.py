"""Setup-only preferences and local Apple asset export; no Python in app startup."""
import configparser
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

home = Path.home()
config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
data = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
state = Path(os.environ.get("XDG_STATE_HOME", home / ".local/state"))
backup = state / "neo-files/backup" / (datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{os.getpid()}")
backup.mkdir(parents=True)

def save(path):
    if path.exists():
        dest = backup / path.relative_to(home)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

query = os.environ["NEO_FILES_XFCONF"]
preferences = {
    "last-menubar-visible": ("bool", "false"),
    "last-statusbar-visible": ("bool", "true"),
    "last-separator-position": ("int", "205"),
    "last-window-width": ("int", "1000"),
    "last-window-height": ("int", "720"),
    "last-side-pane": ("string", "ThunarShortcutsPane"),
    "last-location-bar": ("string", "ThunarLocationButtons"),
    "default-view": ("string", "ThunarIconView"),
    "last-icon-view-zoom-level": ("string", "THUNAR_ZOOM_LEVEL_75_PERCENT"),
    "misc-single-click": ("bool", "false"),
    "misc-use-csd": ("bool", "false"),
    "misc-text-beside-icons": ("bool", "false"),
    "misc-symbolic-icons-in-toolbar": ("bool", "true"),
    "misc-symbolic-icons-in-sidepane": ("bool", "true"),
    "shortcuts-icon-size": ("string", "THUNAR_ICON_SIZE_24"),
    "last-toolbar-items": ("string", "back:1,forward:1,location-bar:1,view-switcher:1,search:1,menu:1"),
}
old = subprocess.run([query, "-c", "thunar", "-lv"], text=True, capture_output=True, timeout=15)
(backup / "thunar-preferences.txt").write_text(old.stdout + old.stderr)
save(config / "xfce4/xfconf/xfce-perchannel-xml/thunar.xml")
for name, (kind, value) in preferences.items():
    args = [query, "-c", "thunar", "-p", "/" + name]
    exists = subprocess.run(args, capture_output=True, timeout=15).returncode == 0
    if not exists:
        args += ["-n", "-t", kind]
    subprocess.run(args + ["-s", value], check=True, timeout=15)

icons = data / "icons/NeoBlushFiles"
for context in ("actions", "places"):
    (icons / "scalable" / context).mkdir(parents=True, exist_ok=True)
(icons / "index.theme").write_text('''[Icon Theme]
Name=Neo Blush Files
Comment=Local SF outlines with native document and device fallbacks
Inherits=Adwaita,breeze,hicolor
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
symbols = {
    "actions/go-previous": "chevron.left", "actions/go-next": "chevron.right",
    "actions/go-up": "chevron.up", "actions/edit-find": "magnifyingglass",
    "actions/view-grid": "square.grid.2x2", "actions/view-list-details": "list.bullet",
    "actions/view-list-icons": "square.grid.2x2", "actions/open-menu": "ellipsis.circle",
    "actions/window-close": "xmark", "actions/tab-new": "plus",
    "places/user-home": "house", "places/user-trash": "trash",
    "places/folder": "folder.fill", "places/inode-directory": "folder.fill",
    "places/folder-download": "arrow.down.circle", "places/folder-downloads": "arrow.down.circle",
    "places/user-desktop": "desktopcomputer", "places/folder-pictures": "photo",
    "places/folder-music": "music.note", "places/folder-videos": "film",
    "places/folder-documents": "doc.text", "places/drive-harddisk": "externaldrive",
    "places/network-workgroup": "network",
}
font_path = data / "fonts/neo-control-center-apple/SF-Pro-Text-Regular.otf"
map_path = state / "neo-control-center/apple-assets/symbol-map.json"
manifest = {}
if font_path.exists() and map_path.exists():
    mapping = json.loads(map_path.read_text())
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
        scale = 20 / max(x1-x0, y1-y0)
        tx, ty = 12-scale*(x0+x1)/2, 12+scale*(y0+y1)/2
        pen = SVGPathPen(glyphs)
        glyph.draw(pen)
        for symbolic in (False, True):
            color = "#000000" if symbolic else "#bd779e" if symbol == "folder.fill" else "#65535f"
            suffix = "-symbolic" if symbolic else ""
            path = icons / "scalable" / f"{target}{suffix}.svg"
            path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
                            f'<path fill="{color}" transform="matrix({scale} 0 0 {-scale} {tx} {ty})" '
                            f'd="{pen.getCommands()}"/></svg>\n')
        manifest[target] = {"symbol": symbol, "codepoint": f"U+{cp:X}", "glyph": cmap[cp], "font": str(font_path)}
    font.close()
(icons / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")

mime = config / "mimeapps.list"
save(mime)
ini = configparser.ConfigParser(interpolation=None, strict=False, delimiters=("=",))
ini.optionxform = str
if mime.exists():
    ini.read(mime)
if not ini.has_section("Default Applications"):
    ini.add_section("Default Applications")
ini["Default Applications"]["inode/directory"] = "thunar.desktop;"
mime.parent.mkdir(parents=True, exist_ok=True)
# Home Manager owns its symlink; the user-only installer merges mutable settings.
if len(sys.argv) > 1 or not mime.is_symlink():
    if mime.is_symlink():
        mime.unlink()
    with mime.open("w") as output:
        ini.write(output, space_around_delimiters=False)

if len(sys.argv) > 1:
    runtime_hypr = config / "hypr/hyprland.lua"
    if runtime_hypr.exists() and os.access(runtime_hypr, os.W_OK):
        old = runtime_hypr.read_text()
        new = re.sub(r'^local fileManager\s*=.*$',
                     'local fileManager = os.getenv("HOME") .. "/.local/bin/neo-files"',
                     old, flags=re.MULTILINE)
        if new != old:
            save(runtime_hypr)
            runtime_hypr.resolve().write_text(new)
    runtime_bar = config / "waybar/config"
    if runtime_bar.exists() and os.access(runtime_bar, os.W_OK):
        bar = json.loads(runtime_bar.read_text())
        bars = bar if isinstance(bar, list) else [bar]
        changed = False
        for entry in bars:
            rewrite = entry.get("hyprland/window", {}).get("rewrite", {})
            if rewrite.get("[Tt]hunar") != "Files":
                rewrite["[Tt]hunar"] = "Files"
                changed = True
            actions = entry.get("custom/desktop", {}).get("menu-actions", {})
            command = str(home / ".local/bin/neo-files")
            if "files" in actions and actions["files"] != command:
                actions["files"] = command
                changed = True
        if changed:
            save(runtime_bar)
            runtime_bar.resolve().write_text(json.dumps(bar, ensure_ascii=False, indent=2) + "\n")
print(f"Thunar configured with {len(manifest)} local SF icons. Backup: {backup}")
