"""Interactive Neo Blush notification settings."""

from pathlib import Path
import argparse
import sys
import gi
from policy import apply, applications, preferences, record_app, save_preference


def cc_call(method, parameters=None):
    from gi.repository import Gio
    return Gio.bus_get_sync(Gio.BusType.SESSION, None).call_sync(
        "org.erikreider.swaync.cc", "/org/erikreider/swaync/cc",
        "org.erikreider.swaync.cc", method, parameters, None,
        Gio.DBusCallFlags.NONE, 1500, None)


def launch():
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gio, GLib, Gtk, Pango
    GLib.set_prgname("neo-notification-settings")

    def label(text, style=None):
        widget = Gtk.Label(label=text, xalign=0)
        if style:
            widget.get_style_context().add_class(style)
        return widget

    def chooser(value, callback, inherit=False):
        widget = Gtk.ComboBoxText()
        if inherit:
            widget.append("default", "Use default")
        for key, title in (("enabled", "Show"), ("muted", "Quiet"), ("ignored", "Block")):
            widget.append(key, title)
        widget.set_active_id(value)
        widget.connect("changed", lambda combo: callback(combo.get_active_id()))
        return widget

    class Settings(Gtk.Application):
        def __init__(self):
            super().__init__(application_id="local.neo.NotificationSettings")
            self.window = None
            self.snapshot = None
            self.syncing = False

        def do_activate(self):
            if self.window:
                self.window.present()
                return
            provider = Gtk.CssProvider()
            provider.load_from_path(str(Path(__file__).with_name("style.css")))
            Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            self.window = Gtk.ApplicationWindow(application=self, title="Notification Settings")
            self.window.get_style_context().add_class("neo-notification-settings")
            display = Gdk.Display.get_default()
            monitor = display.get_primary_monitor() or display.get_monitor(0)
            area = monitor.get_workarea()
            # Leave room for the menu bar, gutters, and client-side title bar.
            self.window.set_default_size(min(570, area.width - 64), min(630, area.height - 140))
            self.window.set_position(Gtk.WindowPosition.CENTER)
            self.window.connect("key-press-event", self.key_pressed)
            self.window.connect("destroy", lambda *_: self.quit())
            header = Gtk.HeaderBar(title="Notifications", show_close_button=True)
            self.window.set_titlebar(header)
            root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            root.set_border_width(20)
            self.window.add(root)
            intro = label("Choose which apps can notify you.", "intro")
            root.pack_start(intro, False, False, 0)
            self.dnd = Gtk.Switch(valign=Gtk.Align.CENTER)
            self.dnd.connect("notify::active", self.change_dnd)
            root.pack_start(self.setting_row("Do Not Disturb", "Pause notification popups.", self.dnd), False, False, 0)
            self.default_choice = chooser(preferences()["default"], lambda mode: self.change(None, mode))
            root.pack_start(self.setting_row("Default delivery", "Used by apps without a specific choice.", self.default_choice), False, False, 0)
            legend = label("Show: popups + center   ·   Quiet: center only   ·   Block: hide", "secondary")
            legend.set_line_wrap(True)
            root.pack_start(legend, False, False, 0)
            section = Gtk.Box(spacing=12)
            section.pack_start(label("APPLICATIONS", "section-label"), True, True, 0)
            add = Gtk.Button(label="Add App…")
            add.connect("clicked", self.add_app)
            section.pack_end(add, False, False, 0)
            root.pack_start(section, False, False, 0)
            self.search = Gtk.SearchEntry(placeholder_text="Search applications")
            self.search.connect("search-changed", lambda *_: self.filter_rows())
            root.pack_start(self.search, False, False, 0)
            scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
            scroll.set_min_content_height(100)
            self.list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            self.list.get_style_context().add_class("app-list")
            scroll.add(self.list)
            root.pack_start(scroll, True, True, 0)
            self.empty = label("Apps appear here when they send a notification.", "secondary")
            self.empty.set_line_wrap(True)
            self.empty.set_no_show_all(True)
            root.pack_start(self.empty, False, False, 0)
            self.status = label("Changes save automatically.", "secondary")
            self.status.set_line_wrap(True)
            root.pack_start(self.status, False, False, 0)
            self.retry = Gtk.Button(label="Apply saved settings")
            self.retry.connect("clicked", lambda *_: self.apply_saved())
            self.retry.set_no_show_all(True)
            root.pack_start(self.retry, False, False, 0)
            self.refresh()
            GLib.timeout_add_seconds(2, self.refresh)
            self.window.show_all()
            self.filter_rows()

        def setting_row(self, title, description, control):
            row = Gtk.Box(spacing=16)
            row.get_style_context().add_class("setting-row")
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            text.pack_start(label(title, "row-title"), False, False, 0)
            subtitle = label(description, "secondary")
            subtitle.set_line_wrap(True)
            text.pack_start(subtitle, False, False, 0)
            row.pack_start(text, True, True, 0)
            row.pack_end(control, False, False, 0)
            return row

        def refresh(self):
            try:
                apps = applications()
                prefs = preferences()
                self.syncing = True
                if self.snapshot is None or apps != self.snapshot[0]:
                    for child in self.list.get_children():
                        self.list.remove(child)
                    for name in sorted(apps, key=str.casefold):
                        row = Gtk.Box(spacing=12)
                        row.get_style_context().add_class("application-row")
                        row.sender_name = name
                        desktop = apps[name].get("desktop-entry", "")
                        appinfo = Gio.DesktopAppInfo.new(desktop + ".desktop") if desktop else None
                        image = (Gtk.Image.new_from_gicon(appinfo.get_icon(), Gtk.IconSize.DIALOG)
                                 if appinfo and appinfo.get_icon() else
                                 Gtk.Image.new_from_icon_name("preferences-system-notifications-symbolic", Gtk.IconSize.DIALOG))
                        image.set_pixel_size(28)
                        row.pack_start(image, False, False, 0)
                        title = label(name or "Unnamed application", "row-title")
                        title.set_ellipsize(Pango.EllipsizeMode.END)
                        title.set_max_width_chars(24)
                        title.set_tooltip_text(name)
                        row.pack_start(title, True, True, 0)
                        row.choice = chooser(prefs["apps"].get(name, "default"),
                                             lambda mode, app=name: self.change(app, mode), True)
                        row.pack_end(row.choice, False, False, 0)
                        self.list.pack_start(row, False, False, 0)
                    self.list.show_all()
                    self.filter_rows()
                # Update controls in place so keyboard focus stays on the app
                # being edited after saving or a background refresh.
                self.default_choice.set_active_id(prefs["default"])
                for row in self.list.get_children():
                    row.choice.set_active_id(prefs["apps"].get(row.sender_name, "default"))
                self.snapshot = (apps, prefs)
                try:
                    self.dnd.set_active(cc_call("GetDnd").unpack()[0])
                    self.dnd.set_sensitive(True)
                    self.dnd.set_tooltip_text(None)
                except GLib.Error:
                    self.dnd.set_sensitive(False)
                    self.dnd.set_tooltip_text("Notification service is unavailable")
                finally:
                    self.syncing = False
            except (OSError, ValueError) as error:
                self.syncing = False
                self.status.set_text("Could not read settings: " + str(error))
            return True

        def filter_rows(self):
            query = self.search.get_text().casefold()
            count = 0
            visible_rows = []
            for row in self.list.get_children():
                visible = query in row.sender_name.casefold()
                row.set_visible(visible)
                context = row.get_style_context()
                context.remove_class("first")
                context.remove_class("last")
                if visible:
                    visible_rows.append(row)
                count += visible
            if visible_rows:
                visible_rows[0].get_style_context().add_class("first")
                visible_rows[-1].get_style_context().add_class("last")
            self.empty.set_text("No matching applications." if query else
                                "Apps appear here when they send a notification.")
            self.empty.set_visible(count == 0)

        def change(self, app, mode):
            if self.syncing:
                return
            try:
                save_preference(app, mode)
                self.apply_saved()
                self.refresh()
            except (OSError, ValueError) as error:
                self.status.set_text("Could not save settings: " + str(error))

        def apply_saved(self):
            try:
                apply()
                cc_call("ReloadConfig")
                self.status.set_text("Saved and applied. Changes affect new notifications.")
                self.retry.hide()
            except (OSError, ValueError, GLib.Error) as error:
                self.status.set_text("Settings saved; could not apply: " + str(error))
                self.retry.show()

        def change_dnd(self, switch, _property):
            if self.syncing:
                return
            try:
                cc_call("SetDnd", GLib.Variant("(b)", (switch.get_active(),)))
            except GLib.Error:
                self.status.set_text("Could not change Do Not Disturb. Try again.")
                self.refresh()

        def add_app(self, _button):
            dialog = Gtk.Dialog(title="Add application", transient_for=self.window, modal=True)
            dialog.get_style_context().add_class("neo-notification-settings")
            dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Add", Gtk.ResponseType.OK)
            area = dialog.get_content_area()
            area.set_border_width(20)
            area.set_spacing(12)
            info = label("Enter the exact notification sender name.\nApps are also added automatically when they notify you.", "secondary")
            area.pack_start(info, False, False, 0)
            entry = Gtk.Entry(placeholder_text="Application name", activates_default=True, max_length=512)
            area.pack_start(entry, False, False, 0)
            dialog.set_default_response(Gtk.ResponseType.OK)
            ok = dialog.get_widget_for_response(Gtk.ResponseType.OK)
            ok.set_sensitive(False)
            entry.connect("changed", lambda widget: ok.set_sensitive(bool(widget.get_text().strip())))
            dialog.show_all()
            if dialog.run() == Gtk.ResponseType.OK:
                try:
                    record_app(entry.get_text().strip(), "")
                    self.refresh()
                except (OSError, ValueError) as error:
                    self.status.set_text("Could not add application: " + str(error))
            dialog.destroy()

        def key_pressed(self, _window, event):
            if event.keyval == Gdk.KEY_Escape:
                self.quit()
                return True
            if event.keyval == Gdk.KEY_f and event.state & Gdk.ModifierType.CONTROL_MASK:
                self.search.grab_focus()
                return True
            return False

    try:
        cc_call("SetVisibility", GLib.Variant("(b)", (False,)))
    except GLib.Error:
        pass
    return Settings().run([sys.argv[0]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Generate runtime config before SwayNC starts")
    parser.add_argument("--monitor", action="store_true", help="Discover notification senders")
    args = parser.parse_args()
    if args.apply:
        apply()
        return 0
    if args.monitor:
        from monitor import run
        run()
        return 0
    return launch()


if __name__ == "__main__":
    sys.exit(main())
