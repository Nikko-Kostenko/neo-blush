"""Discover senders from notification calls, including currently blocked apps."""

import signal
from gi.repository import Gio, GLib
from policy import record_app


def run():
    loop = GLib.MainLoop()
    # A dedicated connection is essential: BecomeMonitor cannot share GTK's bus.
    connection = Gio.DBusConnection.new_for_address_sync(
        Gio.dbus_address_get_for_bus_sync(Gio.BusType.SESSION, None),
        Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT
        | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION, None, None)

    def received(_connection, message, incoming, _data):
        if (incoming and message.get_message_type() == Gio.DBusMessageType.METHOD_CALL
                and message.get_interface() == "org.freedesktop.Notifications"
                and message.get_member() == "Notify"
                and message.get_signature() == "susssasa{sv}i"):
            body = message.get_body()
            name = body.get_child_value(0).get_string()
            hints = body.get_child_value(6)
            entry = hints.lookup_value("desktop-entry", GLib.VariantType.new("s"))
            GLib.idle_add(record_app, name, entry.get_string() if entry else "")
            # Consume monitored calls; dispatch must not reply on a monitor bus.
            return None
        return message

    connection.add_filter(received, None)
    connection.call_sync(
        "org.freedesktop.DBus", "/org/freedesktop/DBus",
        "org.freedesktop.DBus.Monitoring", "BecomeMonitor",
        GLib.Variant("(asu)", ([
            "type='method_call',interface='org.freedesktop.Notifications',member='Notify'"
        ], 0)), None, Gio.DBusCallFlags.NONE, 3000, None)
    connection.connect("closed", lambda *_: loop.quit())
    for signum in (signal.SIGTERM, signal.SIGINT):
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signum, lambda: (loop.quit(), False)[1])
    try:
        loop.run()
    finally:
        if not connection.is_closed():
            connection.close_sync(None)
