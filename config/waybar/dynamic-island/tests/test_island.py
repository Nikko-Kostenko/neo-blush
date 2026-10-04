from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import Island


class IslandTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.island = Island(clock=lambda: self.now)

    def test_initial_device_state_does_not_flash(self):
        self.island.set_audio((40, False))
        self.island.set_brightness(70)
        self.assertEqual(self.island.render()["class"], "idle")
        self.island.set_audio((40, False))
        self.assertEqual(self.island.render()["class"], "idle")

    def test_transient_returns_to_playback_after_latest_change(self):
        self.island.players = {"spotify": {"PlaybackStatus": "Playing", "Metadata": {"xesam:title": "Song"}}}
        self.island.set_audio((40, False))
        self.island.set_audio((45, False))
        self.now = 2
        self.island.set_audio((50, False))
        self.now = 3.5
        self.assertEqual(self.island.render()["class"], "volume")
        self.now = 5.1
        self.assertEqual(self.island.render()["class"], "playing")

    def test_playing_player_selected_over_paused_and_stopped_players(self):
        self.island.players = {"browser": {"PlaybackStatus": "Paused"},
                               "stopped": {"PlaybackStatus": "Stopped"},
                               "spotify": {"PlaybackStatus": "Playing"}}
        self.assertEqual(self.island.selected_player()[0], "spotify")

    def test_untrusted_metadata_is_escaped_and_single_line(self):
        self.island.players = {"test": {"PlaybackStatus": "Playing", "Metadata": {
            "xesam:title": '<span>Title &\nsubtitle</span>', "xesam:artist": ["A & B"]}}}
        text = self.island.render()["text"]
        self.assertIn("&lt;span&gt;", text)
        self.assertIn("A &amp; B", text)
        self.assertNotIn("\n", text)

    def test_mute_change_shows_notice_without_volume_change(self):
        self.island.set_audio((40, False))
        self.island.set_audio((40, True))
        self.assertIn("Muted", self.island.render()["text"])
        self.assertIn("○○○○○○○", self.island.render()["text"])

    def test_missing_audio_does_not_produce_a_false_notice(self):
        self.island.set_audio(None)
        self.island.set_audio((60, False))
        self.assertEqual(self.island.render()["class"], "idle")

    def test_brightness_notice_expires_to_idle(self):
        self.island.set_brightness(50)
        self.island.set_brightness(55)
        self.assertEqual(self.island.render()["class"], "brightness")
        self.now = 3.1
        self.assertEqual(self.island.render()["class"], "idle")
