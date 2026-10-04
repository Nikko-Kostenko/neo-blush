"""Dynamic Island presentation, independent of the desktop event listeners."""

from html import escape
import math
import time

SYMBOLS = {
    "waveform": "\U0010066b", "music": "\U0010046a",
    "speaker": "\U001002a9", "muted": "\U001002a3",
    "sun": "\U001001ae", "pause": "\U00100286",
}


def short(text, limit):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


class Island:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.audio = None
        self.brightness = None
        self.players = {}
        self.notice = None
        self.notice_until = 0

    def set_audio(self, value):
        if value is not None and self.audio is not None and value != self.audio:
            self.flash("volume")
        self.audio = value

    def set_brightness(self, value):
        if value is not None and self.brightness is not None and value != self.brightness:
            self.flash("brightness")
        self.brightness = value

    def flash(self, kind):
        self.notice = kind
        self.notice_until = self.clock() + 3

    def selected_player(self):
        players = [(name, data) for name, data in self.players.items()
                   if data.get("PlaybackStatus") in ("Playing", "Paused")]
        return next(((name, data) for name, data in players
                     if data.get("PlaybackStatus") == "Playing"), players[0] if players else (None, {}))

    def render(self):
        kind = self.notice if self.clock() < self.notice_until else None
        if kind == "volume" and self.audio is not None:
            value, muted = self.audio
            glyph = SYMBOLS["muted" if muted else "speaker"]
            text = f"{glyph}  {'Muted' if muted else 'Sound'}  {value}%"
            return self.level(text, 0 if muted else value, "volume")
        if kind == "brightness" and self.brightness is not None:
            return self.level(f'{SYMBOLS["sun"]}  Display  {self.brightness}%', self.brightness, "brightness")

        name, data = self.selected_player()
        if name:
            metadata = data.get("Metadata", {})
            title = metadata.get("xesam:title") or "Media"
            artists = metadata.get("xesam:artist", [])
            artist = ", ".join(artists) if isinstance(artists, (list, tuple)) else str(artists)
            playing = data["PlaybackStatus"] == "Playing"
            glyph = SYMBOLS["waveform" if playing else "pause"]
            text = f'{glyph}  {escape(short(title, 32))}'
            if artist:
                text += f'  <span foreground="#e1adc9" size="smaller">{escape(short(artist, 20))}</span>'
            return {"text": text, "class": "playing" if playing else "paused",
                    "tooltip": escape(f"{title}\n{artist}\nClick: play/pause · Right click: Control Center\nScroll: volume")}
        return {"text": SYMBOLS["waveform"], "class": "idle",
                "tooltip": "Dynamic Island · No active media\nClick: Control Center · Scroll: volume"}

    @staticmethod
    def level(text, value, kind):
        filled = max(0, min(7, math.ceil(value * 7 / 100)))
        dots = "●" * filled + "○" * (7 - filled)
        return {"text": f'{text}   <span foreground="#f0bad7" size="9000">{dots}</span>',
                "class": kind, "tooltip": "Scroll: volume · Right click: Control Center"}
