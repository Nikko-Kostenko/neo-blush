"""Stream live Dynamic Island state to Waybar using its native custom module."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

from model import Island

STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "neo-dynamic-island"
PLAYER_PREFIX = "org.mpris.MediaPlayer2."


def action(name):
    if name in ("louder", "quieter"):
        args = ["wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SINK@",
                "5%+" if name == "louder" else "5%-"]
    elif name == "toggle":
        try:
            player = json.loads((STATE / "player.json").read_text()).get("player")
        except (OSError, ValueError):
            player = None
        args = (["playerctl", "--player=" + player, "play-pause"] if player else
                [str(Path.home() / ".local/bin/neo-control-center")])
    else:
        args = [str(Path.home() / ".local/bin/neo-control-center")]
    try:
        return subprocess.run(args, timeout=3, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode
    except (OSError, subprocess.TimeoutExpired):
        return 1


def audio_level():
    try:
        result = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                                capture_output=True, text=True, timeout=1,
                                env={**os.environ, "LC_ALL": "C"})
        match = re.search(r"Volume:\s+([0-9.]+)", result.stdout)
        if result.returncode == 0 and match:
            return round(float(match[1]) * 100), "[MUTED]" in result.stdout
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


class Stream:
    def __init__(self):
        from gi.repository import Gio, GLib
        self.Gio, self.GLib = Gio, GLib
        self.loop = GLib.MainLoop()
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.model = Island()
        self.workers = ThreadPoolExecutor(max_workers=2)
        self.stopping = False
        self.last = None
        self.saved_player = object()
        self.pending = {}
        self.running = set()
        self.dirty = set()
        self.audio_process = None
        self.audio_buffer = b""
        self.audio_retry = None
        self.expiry_timer = None
        self.backlight = next((p for p in sorted(Path("/sys/class/backlight").glob("*"))
                               if (p / "brightness").is_file()), None)

    def call(self, bus, path, interface, method, parameters=None):
        return self.bus.call_sync(bus, path, interface, method, parameters, None,
                                  self.Gio.DBusCallFlags.NONE, 350, None).unpack()

    def media(self):
        names = self.call("org.freedesktop.DBus", "/org/freedesktop/DBus",
                          "org.freedesktop.DBus", "ListNames")[0]
        players = {}
        for name in sorted(n for n in names if n.startswith(PLAYER_PREFIX)):
            try:
                players[name[len(PLAYER_PREFIX):]] = self.call(
                    name, "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties",
                    "GetAll", self.GLib.Variant("(s)", ("org.mpris.MediaPlayer2.Player",)))[0]
            except self.GLib.Error:
                # A player may vanish between the signal and the property read.
                continue
        return players

    def request(self, kind):
        if kind in self.running:
            self.dirty.add(kind)
        elif kind not in self.pending:
            self.pending[kind] = self.GLib.timeout_add(150, self.read, kind)

    def read(self, kind):
        self.pending.pop(kind, None)
        self.running.add(kind)
        future = self.workers.submit(self.media if kind == "media" else audio_level)
        future.add_done_callback(lambda f: self.GLib.idle_add(self.finish, kind, f))
        return False

    def finish(self, kind, future):
        self.running.discard(kind)
        if self.stopping:
            return False
        try:
            value = future.result()
        except Exception:
            value = {} if kind == "media" else None
        if kind == "media":
            self.model.players = value
        else:
            self.model.set_audio(value)
        self.publish()
        if kind in self.dirty:
            self.dirty.remove(kind)
            self.request(kind)
        return False

    def publish(self):
        player, _ = self.model.selected_player()
        if player != self.saved_player:
            STATE.mkdir(parents=True, exist_ok=True)
            temporary = STATE / "player.tmp"
            temporary.write_text(json.dumps({"player": player}))
            temporary.replace(STATE / "player.json")
            self.saved_player = player
        result = self.model.render()
        if result != self.last:
            try:
                print(json.dumps(result, ensure_ascii=False), flush=True)
            except BrokenPipeError:
                self.loop.quit()
                return
            self.last = result
        if self.model.notice_until > self.model.clock():
            if self.expiry_timer is not None:
                self.GLib.source_remove(self.expiry_timer)
            remaining = self.model.notice_until - self.model.clock()
            self.expiry_timer = self.GLib.timeout_add(max(1, int(remaining * 1000) + 25), self.expire)

    def expire(self):
        self.expiry_timer = None
        self.publish()
        return False

    def properties_changed(self, connection, sender, path, interface, signal_name, parameters):
        interface, changed, invalidated = parameters.unpack()
        if (interface == "org.mpris.MediaPlayer2.Player"
                and {"PlaybackStatus", "Metadata"}.intersection(set(changed) | set(invalidated))):
            self.request("media")

    def owner_changed(self, connection, sender, path, interface, signal_name, parameters):
        if parameters.unpack()[0].startswith(PLAYER_PREFIX):
            self.request("media")

    def brightness(self):
        if self.backlight:
            try:
                value = int((self.backlight / "brightness").read_text())
                maximum = int((self.backlight / "max_brightness").read_text())
                self.model.set_brightness(round(value * 100 / maximum))
                self.publish()
            except (OSError, ValueError, ZeroDivisionError):
                pass
        return not self.stopping

    def subscribe_audio(self):
        self.audio_retry = None
        if self.stopping:
            return False
        self.audio_buffer = b""
        self.audio_process = subprocess.Popen(["pactl", "subscribe"], stdout=subprocess.PIPE,
                                              stderr=subprocess.DEVNULL,
                                              env={**os.environ, "LC_ALL": "C"})
        os.set_blocking(self.audio_process.stdout.fileno(), False)
        self.GLib.io_add_watch(self.audio_process.stdout.fileno(),
                               self.GLib.IO_IN | self.GLib.IO_HUP | self.GLib.IO_ERR,
                               self.audio_event)
        self.request("audio")
        return False

    def audio_event(self, fd, conditions):
        try:
            data = os.read(fd, 65536)
        except BlockingIOError:
            return True
        if not data:
            self.audio_process.stdout.close()
            self.audio_process.wait(timeout=1)
            self.audio_process = None
            if not self.stopping:
                self.audio_retry = self.GLib.timeout_add_seconds(5, self.subscribe_audio)
            return False
        self.audio_buffer += data
        while b"\n" in self.audio_buffer:
            line, self.audio_buffer = self.audio_buffer.split(b"\n", 1)
            if b"on sink #" in line or b"on server #" in line:
                self.request("audio")
        return True

    def run(self):
        from gi.repository import GLibUnix
        self.bus.signal_subscribe(None, "org.freedesktop.DBus.Properties", "PropertiesChanged",
                                  "/org/mpris/MediaPlayer2", None,
                                  self.Gio.DBusSignalFlags.NONE, self.properties_changed)
        self.bus.signal_subscribe("org.freedesktop.DBus", "org.freedesktop.DBus", "NameOwnerChanged",
                                  "/org/freedesktop/DBus", None,
                                  self.Gio.DBusSignalFlags.NONE, self.owner_changed)
        GLibUnix.signal_add(self.GLib.PRIORITY_DEFAULT, signal.SIGTERM, self.stop)
        self.publish()
        self.request("media")
        self.subscribe_audio()
        self.brightness()
        if self.backlight:
            # Sysfs brightness does not reliably emit file-monitor events.
            # Two tiny file reads per second; no external command or renderer.
            self.GLib.timeout_add_seconds(1, self.brightness)
        try:
            self.loop.run()
        finally:
            self.stopping = True
            if self.audio_process is not None:
                self.audio_process.terminate()
                try:
                    self.audio_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.audio_process.kill()
                    self.audio_process.wait()
            self.workers.shutdown(wait=False, cancel_futures=True)

    def stop(self):
        self.loop.quit()
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=["toggle", "controls", "louder", "quieter"])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return subprocess.run([sys.executable, "-m", "unittest", "discover", "-v",
                               "-s", str(Path(__file__).with_name("tests"))],
                              cwd=Path(__file__).parent).returncode
    if args.action:
        return action(args.action)
    Stream().run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
