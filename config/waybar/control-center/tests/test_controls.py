from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend


class DesktopStateTests(unittest.TestCase):
    def state(self, responses):
        with patch.object(backend, "query", side_effect=lambda *args: responses.get(args)), \
                patch.object(backend, "battery", return_value="72% · Discharging"):
            return backend.read_state()

    def test_wifi_connection_name_preserves_colons(self):
        state = self.state({
            ("nmcli", "radio", "wifi"): "enabled",
            ("nmcli", "-t", "--escape", "no", "-f", "TYPE,STATE,CONNECTION", "device", "status"):
                "wifi:connected:Home:5GHz\nethernet:disconnected:--",
        })
        self.assertEqual(state["wifi"], {"enabled": True, "text": "Home:5GHz"})

    def test_missing_hardware_disables_controls(self):
        state = self.state({("nmcli", "radio", "wifi"): "enabled"})
        self.assertIsNone(state["wifi"]["enabled"])
        self.assertIsNone(state["bluetooth"]["enabled"])
        self.assertIsNone(state["brightness"])
        self.assertIsNone(state["sound"])
        self.assertIsNone(state["media"])

    def test_bluetooth_reports_connected_device(self):
        state = self.state({
            ("bluetoothctl", "show"): "Controller AA:BB:CC:DD:EE:FF\n\tPowered: yes",
            ("bluetoothctl", "devices", "Connected"): "Device 11:22:33:44:55:66 My Headphones",
        })
        self.assertEqual(state["bluetooth"], {"enabled": True, "text": "My Headphones"})

    def test_disabled_radios_do_not_show_stale_connected_names(self):
        state = self.state({
            ("nmcli", "radio", "wifi"): "disabled",
            ("nmcli", "-t", "--escape", "no", "-f", "TYPE,STATE,CONNECTION", "device", "status"):
                "wifi:connected:Home",
            ("bluetoothctl", "show"): "Controller AA:BB:CC:DD:EE:FF\n\tPowered: no",
            ("bluetoothctl", "devices", "Connected"): "Device 11:22:33:44:55:66 My Headphones",
        })
        self.assertEqual(state["wifi"], {"enabled": False, "text": "Off"})
        self.assertEqual(state["bluetooth"], {"enabled": False, "text": "Off"})

    def test_brightness_and_muted_volume(self):
        state = self.state({
            ("brightnessctl", "--class=backlight", "--machine-readable"):
                "intel_backlight,backlight,450,45%,1000",
            ("wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"): "Volume: 0.38 [MUTED]",
        })
        self.assertEqual(state["brightness"], 45)
        self.assertEqual(state["sound"], {"value": 38, "muted": True})

    def test_playing_player_selected_over_paused_player(self):
        responses = {
            ("playerctl", "--list-all"): "firefox.instance1\nspotify",
            ("playerctl", "--player=firefox.instance1", "status"): "Paused",
            ("playerctl", "--player=spotify", "status"): "Playing",
            ("playerctl", "--player=spotify", "metadata", "xesam:title"): "A Song",
            ("playerctl", "--player=spotify", "metadata", "xesam:artist"): "An Artist",
        }
        with patch.object(backend, "query", side_effect=lambda *args: responses.get(args)):
            self.assertEqual(backend.media(), {"player": "spotify", "status": "Playing",
                                               "title": "A Song", "artist": "An Artist"})

    def test_command_failure_and_timeout_are_reported(self):
        with patch.object(subprocess, "run", return_value=SimpleNamespace(
                returncode=1, stdout="", stderr="Permission denied")):
            with self.assertRaisesRegex(RuntimeError, "Permission denied"):
                backend.command("brightnessctl", "set", "50%")
        with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("bluetoothctl", 3)):
            self.assertIsNone(backend.query("bluetoothctl", "show"))

    def test_keep_awake_can_be_stopped_after_panel_closes(self):
        start = backend.awake_command(False)
        self.assertIn("--unit=neo-keep-awake", start)
        self.assertIn("--what=idle:sleep", start)
        self.assertEqual(backend.awake_command(True),
                         ["systemctl", "--user", "stop", "neo-keep-awake.service"])


# These controller checks use real GTK imports but do not need a display server.
try:
    import main
except ImportError:
    main = None


@unittest.skipIf(main is None, "GTK introspection environment unavailable")
class ControllerTests(unittest.TestCase):
    def test_radio_controls_toggle_each_current_state_once(self):
        for key in ("wifi", "bluetooth"):
            for enabled in (True, False):
                with self.subTest(key=key, enabled=enabled):
                    writes = []
                    sensitivity = []
                    status = []
                    pending = set()
                    def perform(action, args):
                        pending.add(action)
                        writes.append(args)
                    controller = SimpleNamespace(
                        pending=pending, state={key: {"enabled": enabled}},
                        radio_buttons={key: SimpleNamespace(set_sensitive=sensitivity.append)},
                        tiles={key: (None, SimpleNamespace(set_text=status.append))},
                        perform=perform,
                    )
                    main.ControlCenter.toggle_radio(controller, key)
                    main.ControlCenter.toggle_radio(controller, key)
                    expected = (["nmcli", "radio", "wifi"] if key == "wifi"
                                else ["bluetoothctl", "power"])
                    self.assertEqual(writes, [expected + ["off" if enabled else "on"]])
                    self.assertEqual(sensitivity, [False])
                    self.assertEqual(status, ["Turning off…" if enabled else "Turning on…"])

    def test_unavailable_radio_cannot_be_toggled(self):
        controller = SimpleNamespace(pending=set(), state={"wifi": {"enabled": None}},
                                     perform=lambda *_: self.fail("No Wi-Fi hardware"))
        main.ControlCenter.toggle_radio(controller, "wifi")

    def test_hidden_resident_panel_does_not_poll(self):
        controller = SimpleNamespace(visible=False, closing=False)
        self.assertFalse(main.ControlCenter.refresh(controller))

    def test_dismissal_hides_window_and_stops_polling_without_exiting(self):
        events = []
        controller = SimpleNamespace(visible=True, refresh_timer=42,
                                     window=SimpleNamespace(hide=lambda: events.append("hide")),
                                     flush_sliders=lambda: events.append("flush"))
        with patch.object(main.GLib, "source_remove") as remove:
            main.ControlCenter.quit(controller)
        self.assertFalse(controller.visible)
        self.assertIsNone(controller.refresh_timer)
        remove.assert_called_once_with(42)
        self.assertEqual(events, ["hide", "flush"])

    def test_outside_click_dismisses_the_same_opening(self):
        dismissed = []
        controller = SimpleNamespace(visible=True, open_generation=2,
                                     quit=lambda: dismissed.append(True))
        self.assertFalse(main.ControlCenter.dismiss_generation(controller, 2))
        self.assertEqual(dismissed, [True])

    def test_delayed_outside_click_cannot_close_a_new_opening(self):
        controller = SimpleNamespace(visible=True, open_generation=3,
                                     quit=lambda: self.fail("Reopened panel"))
        self.assertFalse(main.ControlCenter.dismiss_generation(controller, 2))

    def test_dismissal_flushes_the_last_debounced_slider_value(self):
        writes = []
        controller = SimpleNamespace(debounce={"sound": 42},
                                     sliders={"sound": (SimpleNamespace(get_value=lambda: 38.6), None)},
                                     write_slider=lambda key, value: writes.append((key, value)))
        with patch.object(main.GLib, "source_remove") as remove:
            main.ControlCenter.flush_sliders(controller)
        remove.assert_called_once_with(42)
        self.assertEqual(writes, [("sound", 39)])

    def test_stale_poll_result_cannot_overwrite_recent_slider_change(self):
        refreshes = []
        controller = SimpleNamespace(polling=True, revision=2,
                                     refresh=lambda: refreshes.append(True))
        self.assertFalse(main.ControlCenter.finish_refresh(controller, {"old": True}, 1))
        self.assertEqual(refreshes, [True])

    def test_pending_slider_stays_pending_until_all_writes_finish(self):
        controller = SimpleNamespace(inflight={"sound": 2}, revision=0,
                                     pending={"sound"}, debounce={}, refresh=lambda: None)
        main.ControlCenter.finish_action(controller, "sound")
        self.assertIn("sound", controller.pending)
        main.ControlCenter.finish_action(controller, "sound")
        self.assertNotIn("sound", controller.pending)


if __name__ == "__main__":
    unittest.main()
