"""Adapt the pinned WhiteSur Qt theme to Neo Blush; no Apple assets here."""
import configparser
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

source, target = map(Path, sys.argv[1:])
target.mkdir(parents=True, exist_ok=True)
recolors = {
    "#0860f2": "#a83f74", "#0852ce": "#903361", "#0e4bb4": "#903361",
    "#3484e2": "#a83f74", "#77aff1": "#dba9c4", "#b74aff": "#bd6b98",
    "#f5f5f5": "#fff3f9", "#f2f2f2": "#f9eaf2", "#fafafa": "#fff8fc",
    "#f9f9f9": "#fff8fc", "#333333": "#452c3b", "#242424": "#452c3b",
    "#424242": "#65535f", "#4d4d4d": "#65535f", "#666666": "#76636f",
    "#a0a0a0": "#a38e9b", "#969696": "#a38e9b", "#c8c8c8": "#e5cfdd",
    "#d2d2d2": "#eddce6", "#eeeeee": "#f2dfea", "#dddddd": "#e5cfdd",
}

def recolor(text):
    return re.sub(r"#[0-9a-fA-F]{6}", lambda m: recolors.get(m[0].lower(), m[0]), text)

theme = configparser.ConfigParser(interpolation=None, strict=False)
theme.optionxform = str
theme.read_string(recolor((source / "WhiteSur.kvconfig").read_text()))
changes = {
    "%General": {
        "comment": "Neo Blush: Finder-inspired Qt controls with quiet file content",
        "dark_titlebar": "false", "toolbar_icon_size": "20", "small_icon_size": "18",
        "layout_spacing": "8", "layout_margin": "8", "scroll_width": "8",
        "transient_scrollbar": "true", "tree_branch_line": "false",
        "reduce_window_opacity": "24", "reduce_menu_opacity": "10",
        "double_click": "true", "respect_DE": "false", "blurring": "false",
        "popup_blurring": "true", "menu_shadow_depth": "4",
    },
    "GeneralColors": {
        "window.color": "#fff3f9", "inactive.window.color": "#fff3f9",
        "base.color": "#fff8fc", "inactive.base.color": "#fff8fc",
        "alt.base.color": "#faf0f6", "inactive.alt.base.color": "#faf0f6",
        "text.color": "#452c3b", "inactive.text.color": "#65535f",
        "window.text.color": "#452c3b", "inactive.window.text.color": "#65535f",
        "button.text.color": "#452c3b", "disabled.text.color": "#9c8895",
        "highlight.color": "#edd0e0", "inactive.highlight.color": "#f0dce7",
        "highlight.text.color": "#452c3b", "inactive.highlight.text.color": "#452c3b",
        "tooltip.base.color": "#fff3f9", "tooltip.text.color": "#452c3b",
    },
    "Hacks": {
        "transparent_dolphin_view": "false", "force_size_grip": "false",
        "single_top_toolbar": "true", "disabled_icon_opacity": "45",
    },
    "Toolbar": {"frame": "false", "interior": "false", "frame.top": "6", "frame.bottom": "6", "frame.left": "10", "frame.right": "10"},
    "MenuItem": {"text.focus.color": "#452c3b", "text.press.color": "#452c3b", "text.toggle.color": "#452c3b"},
    "ItemView": {"text.focus.color": "#452c3b", "text.press.color": "#452c3b", "text.toggle.color": "#452c3b"},
}
for section, values in changes.items():
    for key, value in values.items():
        theme[section][key] = value
with (target / "NeoBlushDolphin.kvconfig").open("w") as output:
    theme.write(output, space_around_delimiters=False)

ET.register_namespace("", "http://www.w3.org/2000/svg")
svg = ET.fromstring(recolor((source / "WhiteSur.svg").read_text()))
# Pale selection material keeps the same dark text on hover and selection.
for element in svg.iter():
    if element.get("id", "").startswith(("menuitem", "itemview")):
        for child in element.iter():
            for key, value in list(child.attrib.items()):
                child.set(key, value.replace("#a83f74", "#edd0e0").replace("#903361", "#d9b7cc"))
ET.ElementTree(svg).write(target / "NeoBlushDolphin.svg", encoding="utf-8", xml_declaration=True)
