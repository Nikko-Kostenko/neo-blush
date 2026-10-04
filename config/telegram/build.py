"""Build the Telegram theme archive from the checked-in color palette."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "Neo-Blush.tdesktop-theme"


with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
    for name, data in (
        ("colors.tdesktop-theme", (ROOT / "colors.tdesktop-theme").read_bytes()),
        ("background.png", (ROOT / "background-frosted.png").read_bytes()),
    ):
        info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        archive.writestr(info, data)

print(OUTPUT)
