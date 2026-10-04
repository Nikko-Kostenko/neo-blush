"""Export genuine local SF Pro outlines; proprietary assets stay outside the repo."""
import argparse
import json
from pathlib import Path
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = Path.home() / ".local/state/neo-control-center/apple-assets"
    parser.add_argument("--font", type=Path, default=source / "extracted/Library/Fonts/SF-Pro-Text-Regular.otf")
    parser.add_argument("--mapping", type=Path, default=source / "symbol-map.json")
    parser.add_argument("--symbols", type=Path, default=Path(__file__).with_name("symbols.json"))
    parser.add_argument("--output", type=Path, default=Path.home() / ".local/share/vivaldi-neo/icons")
    args = parser.parse_args()
    mapping = json.loads(args.mapping.read_text())
    symbols = json.loads(args.symbols.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    provenance = {}
    with TTFont(args.font) as font:
        glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
        # Validate every selected symbol before writing any exports.
        for button, symbol in symbols.items():
            if symbol not in mapping:
                raise ValueError(f"No local mapping for {symbol}")
            value = mapping[symbol]
            point = ord(value) if len(value) == 1 else int(value.replace("U+", "0x"), 0)
            if point not in cmap or cmap[point] == ".notdef":
                raise ValueError(f"{symbol} is absent from this font")
            name = cmap[point]
            glyph = glyphs[name]
            bounds = BoundsPen(glyphs)
            glyph.draw(bounds)
            if bounds.bounds is None:
                raise ValueError(f"Empty outline for {symbol}")
            x0, y0, x1, y1 = bounds.bounds
            scale = 18 / max(x1 - x0, y1 - y0)
            pen = SVGPathPen(glyphs)
            glyph.draw(pen)
            tx, ty = 12 - scale * (x0 + x1) / 2, 12 + scale * (y0 + y1) / 2
            svg = (
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
                f'<path fill="currentColor" transform="translate({tx:.10g} {ty:.10g}) '
                f'scale({scale:.10g} {-scale:.10g})" d="{pen.getCommands()}"/></svg>\n'
            )
            provenance[button] = {
                "symbol": symbol, "codepoint": f"U+{point:X}", "glyph": name,
                "source_font": str(args.font.resolve()), "canvas": 24, "extent": 18,
                "asset_kind": "monochrome-font-outline", "svg": svg,
            }
    for button, entry in provenance.items():
        (args.output / f"{button}.svg").write_text(entry.pop("svg"))
    (args.output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"Exported {len(provenance)} Apple symbol outlines to {args.output}")


if __name__ == "__main__":
    main()
