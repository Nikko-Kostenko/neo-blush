"""Install fonts and symbol outlines from a user-supplied SF Symbols package.

Run with a Python environment containing fontTools. Pass the extracted
Library/Fonts directory; no Apple assets are included in this repository.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

# Stable PUA mappings checked against qzrzz/SF-Symbols-JSON (SF Symbols 7).
# Bluetooth is not in SF Symbols; retain the theme's Bluetooth drawing.
SYMBOLS = {
    "wifi": ("wifi", 0x100647, 20),
    "wifi-off": ("wifi.slash", 0x100648, 20),
    "network": ("network", 0x100906, 20),
    "moon": ("moon.fill", 0x1001BA, 20),
    "microphone": ("microphone.fill", 0x1002B1, 20),
    "sun": ("sun.max.fill", 0x1001AE, 22),
    "speaker": ("speaker.wave.3.fill", 0x1002A9, 22),
    "speaker-muted": ("speaker.slash.fill", 0x1002A3, 22),
    "music": ("music.note", 0x10046A, 20),
    "play": ("play.fill", 0x100284, 17),
    "pause": ("pause.fill", 0x100286, 17),
    "previous": ("backward.end.fill", 0x10028E, 20),
    "next": ("forward.end.fill", 0x100290, 20),
    "lock": ("lock.fill", 0x1003A1, 20),
    "audio-output": ("airplay.audio", 0x100462, 20),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fonts", type=Path)
    args = parser.parse_args()
    font_names = ["SF-Pro-Text-Regular.otf", "SF-Pro-Text-Medium.otf",
                  "SF-Pro-Text-Semibold.otf", "SF-Pro-Display-Regular.otf"]
    for name in font_names:
        if not (args.fonts / name).is_file():
            parser.error(f"Missing {name} in {args.fonts}")

    data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    icon_dir = data / "neo-control-center/icons"
    font_dir = data / "fonts/neo-control-center-apple"
    font = TTFont(args.fonts / font_names[0])
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    exports, manifest = {}, {}
    for target, (symbol, codepoint, extent) in SYMBOLS.items():
        glyph = glyphs[cmap[codepoint]]
        bounds = BoundsPen(glyphs)
        glyph.draw(bounds)
        x0, y0, x1, y1 = bounds.bounds
        scale = extent / max(x1 - x0, y1 - y0)
        pen = SVGPathPen(glyphs)
        glyph.draw(pen)
        tx, ty = 12 - scale * (x0 + x1) / 2, 12 + scale * (y0 + y1) / 2
        exports[target] = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
            f'<path fill="#000000" transform="translate({tx} {ty}) scale({scale} {-scale})" '
            f'd="{pen.getCommands()}"/></svg>\n'
        )
        manifest[target] = {"symbol": symbol, "codepoint": hex(codepoint),
                            "glyph": cmap[codepoint], "source": str(args.fonts / font_names[0])}
    icon_dir.mkdir(parents=True, exist_ok=True)
    font_dir.mkdir(parents=True, exist_ok=True)
    for name, svg in exports.items():
        (icon_dir / f"neo-{name}-symbolic.svg").write_text(svg)
    for name in font_names:
        shutil.copy2(args.fonts / name, font_dir / name)
    (icon_dir.parent / "apple-assets.json").write_text(json.dumps(manifest, indent=2) + "\n")
    subprocess.run(["fc-cache", "-f", str(font_dir)], check=True)
    print(f"Installed {len(exports)} Apple symbol outlines and {len(font_names)} SF Pro fonts.")


if __name__ == "__main__":
    main()
