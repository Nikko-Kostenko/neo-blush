"""A Wayland Control Center, launched and toggled by Waybar."""

from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from pathlib import Path
import json
import os
import signal
import subprocess
import sys

if __name__ == "__main__" and "--self-test" in sys.argv:
    test_dir = str(Path(__file__).with_name("tests"))
    sys.exit(subprocess.run([sys.executable, "-m", "unittest", "discover", "-v",
                             "-s", test_dir], cwd=Path(__file__).parent).returncode)

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, Gio, GLib, GLibUnix, Gtk, GtkLayerShell, Pango

from backend import awake_command, command, query, read_state


def styled(widget, *classes):
    for name in classes:
        widget.get_style_context().add_class(name)
    return widget


def label(text, *classes):
    widget = styled(Gtk.Label(label=text, xalign=0), *classes)
    widget.set_ellipsize(Pango.EllipsizeMode.END)
    widget.set_max_width_chars(28)
    return widget


def icon(name, size=20):
    name = {
        "network-wireless-symbolic": "neo-wifi-symbolic",
        "bluetooth-active-symbolic": "neo-bluetooth-symbolic",
        "weather-clear-night-symbolic": "neo-moon-symbolic",
        "audio-input-microphone-symbolic": "neo-microphone-symbolic",
        "display-brightness-symbolic": "neo-sun-symbolic",
        "audio-volume-high-symbolic": "neo-speaker-symbolic",
        "audio-volume-muted-symbolic": "neo-speaker-muted-symbolic",
        "audio-x-generic-symbolic": "neo-music-symbolic",
        "media-playback-start-symbolic": "neo-play-symbolic",
        "media-playback-pause-symbolic": "neo-pause-symbolic",
        "media-skip-backward-symbolic": "neo-previous-symbolic",
        "media-skip-forward-symbolic": "neo-next-symbolic",
        "system-lock-screen-symbolic": "neo-lock-symbolic",
        "audio-card-symbolic": "neo-audio-output-symbolic",
    }.get(name, name)
    image = Gtk.Image.new_from_icon_name(name, Gtk.IconSize.BUTTON)
    image.set_pixel_size(size)
    return image


def button(name, tooltip, callback):
    widget = styled(Gtk.Button(), "icon-button")
    widget.set_image(icon(name))
    widget.set_tooltip_text(tooltip)
    widget.get_accessible().set_name(tooltip)
    widget.connect("clicked", callback)
    return widget


class ControlCenter(Gtk.Application):
    def __init__(self, start_hidden=False):
        super().__init__(application_id="local.neo.ControlCenter",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.window = None
        self.visible = False
        self.start_hidden = start_hidden
        self.refresh_timer = None
        self.open_generation = 0
        dismiss = Gio.SimpleAction.new("dismiss", None)
        dismiss.connect("activate", lambda *_: self.request_dismiss())
        self.add_action(dismiss)
        escape = Gio.SimpleAction.new("escape", None)
        escape.connect("activate", lambda *_: self.quit())
        self.add_action(escape)
        # Keep GTK loaded between openings, with no polling while hidden.
        self.hold()
        self.state = {}
        self.syncing = False
        self.polling = False
        self.pending = set()
        self.inflight = Counter()
        self.revision = 0
        self.debounce = {}
        self.reader = ThreadPoolExecutor(max_workers=1)
        self.writer = ThreadPoolExecutor(max_workers=1)
        self.closing = False
        GLibUnix.signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self.stop)

    def do_activate(self):
        if self.window is not None:
            if self.visible:
                self.quit()
            else:
                self.open_panel()
            return
        css = Gtk.CssProvider()
        css.load_from_path(str(Path(__file__).with_name("style.css")))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Gtk.Settings.get_default().set_property("gtk-icon-theme-name", "Adwaita")
        Gtk.IconTheme.get_default().prepend_search_path(str(Path(__file__).with_name("icons")))
        # Local symbol exports can override the bundled drawings without copying
        # proprietary Apple assets into the Nix package.
        local_icons = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "neo-control-center/icons"
        if local_icons.is_dir():
            Gtk.IconTheme.get_default().prepend_search_path(str(local_icons))
        monitor = self.monitor_under_pointer()
        self.window = self.layer_window("neo-control-center", monitor)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.TOP, 58)
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.RIGHT, 18)
        # Only the panel receives pointer input. ON_DEMAND gives it keyboard
        # focus on opening without blocking clicks on other windows or the bar.
        self.overlay = Gtk.Overlay()
        self.window.add(self.overlay)
        GtkLayerShell.set_keyboard_mode(self.window, GtkLayerShell.KeyboardMode.ON_DEMAND)
        self.window.connect("key-press-event", self.key_press)
        self.window.connect("delete-event", lambda *_: self.quit())
        self.build_panel()
        self.overlay.show_all()
        self.error.hide()
        if os.environ.get("NEO_GLASS_REDUCE_TRANSPARENCY") == "1":
            css = Gtk.CssProvider()
            css.load_from_data(b'.glass { background: #fff3f9; }')
            Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)
        if self.start_hidden:
            self.start_hidden = False
        else:
            self.open_panel()

    def open_panel(self):
        monitor = self.monitor_under_pointer()
        GtkLayerShell.set_monitor(self.window, monitor)
        self.error.hide()
        self.visible = True
        self.open_generation += 1
        self.window.show()
        self.refresh()
        self.refresh_timer = GLib.timeout_add_seconds(2, self.refresh)

    def quit(self):
        """Dismiss the panel immediately, preserving GTK for the next opening."""
        self.visible = False
        if self.window is not None:
            self.window.hide()
        if self.refresh_timer is not None:
            GLib.source_remove(self.refresh_timer)
            self.refresh_timer = None
        self.flush_sliders()

    def flush_sliders(self):
        # Closing must preserve the final movement of a debounced slider.
        for key, source in list(self.debounce.items()):
            GLib.source_remove(source)
            self.write_slider(key, round(self.sliders[key][0].get_value()))

    def stop(self):
        Gtk.Application.quit(self)
        return False

    def monitor_under_pointer(self):
        # Hyprland reports global coordinates; GDK's Wayland pointer coordinates
        # are surface-local and cannot select the clicked bar's monitor reliably.
        display = Gdk.Display.get_default()
        if display.get_n_monitors() == 1:
            return display.get_monitor(0)
        try:
            position = json.loads(query("hyprctl", "-j", "cursorpos") or "{}")
            monitors = json.loads(query("hyprctl", "-j", "monitors") or "[]")
            for output in monitors:
                scale = output.get("scale", 1)
                width, height = output["width"], output["height"]
                if output.get("transform", 0) % 2:
                    width, height = height, width
                if (output["x"] <= position["x"] < output["x"] + width / scale
                        and output["y"] <= position["y"] < output["y"] + height / scale):
                    for index in range(display.get_n_monitors()):
                        monitor = display.get_monitor(index)
                        geometry = monitor.get_geometry()
                        if geometry.x == output["x"] and geometry.y == output["y"]:
                            return monitor
        except (ValueError, KeyError, TypeError):
            pass
        return display.get_primary_monitor() or display.get_monitor(0)

    def layer_window(self, namespace, monitor):
        window = Gtk.ApplicationWindow(application=self)
        window.set_name(namespace)
        window.set_decorated(False)
        window.set_resizable(False)
        window.set_app_paintable(True)
        visual = window.get_screen().get_rgba_visual()
        if visual:
            window.set_visual(visual)
        GtkLayerShell.init_for_window(window)
        GtkLayerShell.set_namespace(window, namespace)
        GtkLayerShell.set_layer(window, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_monitor(window, monitor)
        GtkLayerShell.set_exclusive_zone(window, -1)
        return window

    def request_dismiss(self):
        # The compositor observes a mouse release without consuming it. Let the
        # bar finish its own click action before dismissing the same opening.
        if self.visible:
            GLib.timeout_add(80, self.dismiss_generation, self.open_generation)

    def dismiss_generation(self, generation):
        if self.visible and generation == self.open_generation:
            self.quit()
        return False

    def key_press(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.quit()
            return True
        return False

    def build_panel(self):
        # Only the individual controls paint a material; the layout is transparent.
        panel = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12), "panel")
        self.panel = panel
        panel.set_size_request(320, -1)
        panel.set_halign(Gtk.Align.END)
        panel.set_valign(Gtk.Align.START)
        self.overlay.add(panel)
        grid = Gtk.Grid(column_spacing=12, row_spacing=12, column_homogeneous=True)
        panel.pack_start(grid, False, False, 0)

        self.tiles = {}
        self.radio_buttons = {}
        for row_number, (key, title, glyph) in enumerate((
                ("wifi", "Wi-Fi", "network-wireless-symbolic"),
                ("bluetooth", "Bluetooth", "bluetooth-active-symbolic"))):
            capsule = styled(Gtk.Button(), "glass", "connection-capsule")
            capsule.set_size_request(-1, 68)
            capsule.set_sensitive(False)
            capsule.set_tooltip_text(f"Toggle {title}")
            capsule.get_accessible().set_name(f"Toggle {title}")
            capsule.connect("clicked", lambda _, k=key: self.toggle_radio(k))
            row = Gtk.Box(spacing=10)
            capsule.add(row)
            toggle = styled(Gtk.Box(), "radio-glyph")
            toggle.pack_start(icon(glyph, 26), True, True, 0)
            toggle.set_valign(Gtk.Align.CENTER)
            row.pack_start(toggle, False, False, 0)
            texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            texts.pack_start(label(title, "title"), False, False, 0)
            status = label("Checking…", "subtitle")
            status.set_max_width_chars(10)
            texts.pack_start(status, False, False, 0)
            row.pack_start(texts, True, True, 0)
            self.tiles[key] = (toggle, status)
            self.radio_buttons[key] = capsule
            grid.attach(capsule, 0, row_number, 2, 1)

        media = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8), "glass", "media-tile")
        art = styled(Gtk.Box(halign=Gtk.Align.START), "album-art")
        art.pack_start(icon("audio-x-generic-symbolic", 22), True, True, 0)
        media.pack_start(art, False, False, 0)
        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.track = label("Not Playing", "title")
        self.artist = label("", "subtitle")
        for text in (self.track, self.artist):
            text.set_max_width_chars(14)
            texts.pack_start(text, False, False, 0)
        media.pack_start(texts, True, True, 0)
        controls = Gtk.Box(spacing=8, homogeneous=True)
        self.media_buttons = []
        for action, glyph, tooltip in (
                ("previous", "media-skip-backward-symbolic", "Previous"),
                ("play-pause", "media-playback-start-symbolic", "Play / pause"),
                ("next", "media-skip-forward-symbolic", "Next")):
            control = button(glyph, tooltip, lambda _, a=action: self.media_action(a))
            control.set_image(icon(glyph, 24))
            styled(control, "media-button")
            control.set_sensitive(False)
            self.media_buttons.append(control)
            controls.pack_start(control, True, True, 0)
        media.pack_start(controls, False, False, 0)
        grid.attach(media, 2, 0, 2, 2)

        self.awake = styled(Gtk.Button(), "glass", "awake-capsule")
        awake_content = Gtk.Box(spacing=10)
        moon = styled(Gtk.Box(), "toggle-glyph")
        moon.set_valign(Gtk.Align.CENTER)
        moon.pack_start(icon("weather-clear-night-symbolic", 22), True, True, 0)
        awake_content.pack_start(moon, False, False, 0)
        awake_content.pack_start(label("Keep Awake", "title"), True, True, 0)
        self.awake.add(awake_content)
        self.awake.connect("clicked", lambda *_: self.perform("awake", awake_command(self.state.get("awake", False))))
        self.awake.set_tooltip_text("Prevent idle and sleep until switched off; stays on when the panel closes")
        self.awake.get_accessible().set_name("Keep Awake")
        grid.attach(self.awake, 0, 2, 2, 1)
        self.mic = styled(button("audio-input-microphone-symbolic", "Mute microphone",
                                 lambda *_: self.perform("microphone", ["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])),
                          "glass", "round-control", "microphone")
        self.mic.set_sensitive(False)
        self.mic.set_image(icon("audio-input-microphone-symbolic", 26))
        self.mic.set_halign(Gtk.Align.CENTER)
        self.mic.set_valign(Gtk.Align.CENTER)
        self.mic.set_size_request(68, 68)
        grid.attach(self.mic, 2, 2, 1, 1)
        lock = styled(button("system-lock-screen-symbolic", "Lock screen",
                             lambda *_: self.launch("neo-session", "lock")), "glass", "round-control")
        lock.set_image(icon("system-lock-screen-symbolic", 26))
        lock.set_halign(Gtk.Align.CENTER)
        lock.set_valign(Gtk.Align.CENTER)
        lock.set_size_request(68, 68)
        grid.attach(lock, 3, 2, 1, 1)

        self.sliders = {}
        for row_number, (key, title, glyph, minimum) in enumerate((
                ("brightness", "Display", "display-brightness-symbolic", 1),
                ("sound", "Sound", "audio-volume-high-symbolic", 0)), start=3):
            card = styled(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3), "glass", "slider-capsule")
            card.pack_start(label(title, "title"), False, False, 0)
            # GTK exposes the scale value to accessibility; keep the textual
            # value for status updates/tooltips without adding a visual badge.
            value = label("—", "subtitle")
            row = Gtk.Box(spacing=9)
            if key == "sound":
                self.mute = button(glyph, "Mute / unmute",
                                   lambda *_: self.perform("sound", ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"]))
                styled(self.mute, "slider-icon")
                self.mute.set_sensitive(False)
                row.pack_start(self.mute, False, False, 0)
            else:
                row.pack_start(icon(glyph, 16), False, False, 0)
            slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, minimum, 100, 1)
            slider.set_draw_value(False)
            slider.set_hexpand(True)
            slider.set_sensitive(False)
            slider.get_accessible().set_name("Display brightness" if key == "brightness" else "Speaker volume")
            slider.set_tooltip_text("Display brightness" if key == "brightness" else "Speaker volume")
            slider.connect("value-changed", self.slider_changed, key)
            row.pack_start(slider, True, True, 0)
            row.pack_start(icon(glyph, 18), False, False, 0)
            if key == "sound":
                output = styled(button("audio-card-symbolic", "Audio devices and settings",
                                       lambda *_: self.launch("pavucontrol")), "output-button")
                row.pack_end(output, False, False, 0)
            card.pack_start(row, False, False, 0)
            self.sliders[key] = (slider, value)
            grid.attach(card, 0, row_number, 4, 1)

        footer = Gtk.Box(halign=Gtk.Align.CENTER)
        self.battery_capsule = styled(Gtk.Box(spacing=6), "glass", "status-capsule")
        self.battery_capsule.pack_start(icon("battery-symbolic", 14), False, False, 0)
        self.battery = label("", "battery-label")
        self.battery_capsule.pack_start(self.battery, False, False, 0)
        footer.pack_start(self.battery_capsule, False, False, 0)
        panel.pack_start(footer, False, False, 0)
        self.error = styled(label("", "error"), "glass")
        self.error.set_line_wrap(True)
        panel.pack_start(self.error, False, False, 0)

    def refresh(self):
        if not self.visible or self.closing:
            return False
        if not self.polling:
            self.polling = True
            self.reader.submit(self.read_in_background, self.revision)
        return True

    def read_in_background(self, revision):
        try:
            state = read_state()
        except Exception as error:
            GLib.idle_add(self.report_error, str(error))
            GLib.idle_add(self.finish_refresh, None, revision)
        else:
            GLib.idle_add(self.finish_refresh, state, revision)

    def finish_refresh(self, state, revision):
        self.polling = False
        if revision != self.revision:
            self.refresh()
            return False
        if state is None:
            return False
        self.state = state
        self.syncing = True
        try:
            for key, (tile, status) in self.tiles.items():
                if key in self.pending:
                    continue
                value = state[key]
                self.radio_buttons[key].set_sensitive(value["enabled"] is not None)
                self.active(tile, value["enabled"])
                status.set_text(value["text"])
                title = "Wi-Fi" if key == "wifi" else "Bluetooth"
                action = f"Turn {title} {'off' if value['enabled'] else 'on'}"
                control = self.radio_buttons[key]
                control.set_tooltip_text(action if value["enabled"] is not None else f"{title} unavailable")
                control.get_accessible().set_name(action)
            for key, (slider, value) in self.sliders.items():
                if key in self.pending:
                    continue
                data = state[key]
                percent = data["value"] if key == "sound" and data else data
                slider.set_sensitive(percent is not None)
                if percent is not None:
                    slider.set_value(percent)
                    value.set_text("Muted" if key == "sound" and data["muted"] else f"{percent}%")
                else:
                    value.set_text("Unavailable")
                if key == "sound":
                    self.mute.set_sensitive(data is not None)
                    self.mute.set_image(icon("audio-volume-muted-symbolic" if data and data["muted"] else "audio-volume-high-symbolic"))
            if "microphone" not in self.pending:
                mic = state["microphone"]
                self.mic.set_sensitive(mic is not None)
                self.active(self.mic, mic and mic["muted"])
                self.mic.set_tooltip_text("Microphone muted · Click to unmute" if mic and mic["muted"] else "Click to mute microphone")
            if "awake" not in self.pending:
                self.active(self.awake, state["awake"])
            media = state["media"]
            self.track.set_text(media["title"] if media else "Not Playing")
            self.track.set_tooltip_text(media["title"] if media else "Start music or a video")
            self.artist.set_text(media["artist"] if media else "")
            for control in self.media_buttons:
                control.set_sensitive(media is not None and "media" not in self.pending)
            self.media_buttons[1].set_image(icon("media-playback-pause-symbolic" if media and media["status"] == "Playing" else "media-playback-start-symbolic", 24))
            self.battery.set_text(state["battery"])
            self.battery_capsule.set_visible(bool(state["battery"]))
        finally:
            self.syncing = False
        return False

    @staticmethod
    def active(widget, enabled):
        context = widget.get_style_context()
        if enabled:
            context.add_class("active")
        else:
            context.remove_class("active")

    def toggle_radio(self, key):
        if key in self.pending:
            return
        enabled = self.state[key]["enabled"]
        if enabled is None:
            return
        args = ["nmcli", "radio", "wifi", "off" if enabled else "on"] if key == "wifi" else ["bluetoothctl", "power", "off" if enabled else "on"]
        tile, status = self.tiles[key]
        self.radio_buttons[key].set_sensitive(False)
        status.set_text("Turning off…" if enabled else "Turning on…")
        self.perform(key, args)

    def slider_changed(self, slider, key):
        if self.syncing:
            return
        percent = round(slider.get_value())
        self.revision += 1
        self.sliders[key][1].set_text(f"{percent}%")
        self.pending.add(key)
        if key in self.debounce:
            GLib.source_remove(self.debounce.pop(key))
        self.debounce[key] = GLib.timeout_add(100, self.write_slider, key, percent)

    def write_slider(self, key, percent):
        self.debounce.pop(key, None)
        if key == "brightness":
            args = ["brightnessctl", "--class=backlight", "set", f"{max(1, percent)}%"]
        else:
            args = ["wpctl", "set-volume", "--limit", "1", "@DEFAULT_AUDIO_SINK@", f"{percent}%"]
        self.perform(key, args, from_slider=True)
        return False

    def media_action(self, action):
        media = self.state.get("media")
        if media and "media" not in self.pending:
            self.perform("media", ["playerctl", f"--player={media['player']}", action])

    def perform(self, key, args, from_slider=False):
        if key in self.pending and not from_slider:
            return
        self.pending.add(key)
        self.inflight[key] += 1
        self.revision += 1
        self.error.hide()
        self.writer.submit(self.write_in_background, key, args)

    def write_in_background(self, key, args):
        try:
            command(*args, timeout=10)
        except RuntimeError as error:
            GLib.idle_add(self.report_error, str(error))
        GLib.idle_add(self.finish_action, key)

    def finish_action(self, key):
        self.inflight[key] -= 1
        self.revision += 1
        if not self.inflight[key] and key not in self.debounce:
            self.pending.discard(key)
        self.refresh()
        return False

    def report_error(self, text):
        self.error.set_text(text[:180])
        self.error.set_tooltip_text(text)
        self.error.show()
        return False

    def launch(self, *args):
        try:
            Gio.Subprocess.new(list(args), Gio.SubprocessFlags.NONE)
        except GLib.Error as error:
            self.report_error(str(error))
        else:
            self.quit()

    def do_shutdown(self):
        self.closing = True
        self.flush_sliders()
        for window in self.get_windows():
            window.destroy()
        self.reader.shutdown(wait=False, cancel_futures=True)
        self.writer.shutdown(wait=False)
        Gtk.Application.do_shutdown(self)


if __name__ == "__main__":
    start_hidden = "--daemon" in sys.argv
    if start_hidden:
        sys.argv.remove("--daemon")
    sys.exit(ControlCenter(start_hidden=start_hidden).run(sys.argv))
