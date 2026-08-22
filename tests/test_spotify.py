from unittest.mock import patch

from core.action_parser import parse_actions
from tools.spotify import play_track


def test_parse_artist():
    action = parse_actions("mets du Damso")[0]
    assert action["action"] == "PLAY_MUSIC"
    assert action["artist"] == "damso"


def test_parse_track_and_artist():
    action = parse_actions("mets Mosaïque Solitaire de Damso")[0]
    assert action["title"] == "mosaique solitaire"
    assert action["artist"] == "damso"


def test_parse_compound_open_and_play():
    actions = parse_actions("ouvre spotify met damso feu de bois")
    assert actions[0] == {"action": "OPEN_APPLICATION", "target": "spotify"}
    assert actions[1]["artist"] == "damso"
    assert actions[1]["title"] == "feu de bois"


def test_play_track():
    with patch("tools.spotify.subprocess.Popen") as popen:
        ok, message = play_track("Mosaïque Solitaire", "Damso")
    assert ok is True
    assert "Damso" in message
    popen.assert_called_once()


def test_spotify_failure():
    with patch("tools.spotify.subprocess.Popen", side_effect=OSError("absent")):
        ok, _ = play_track("Damso")
    assert ok is False
