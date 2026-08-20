from core.intent import detect_intent
from core import dispatcher
from unittest.mock import patch


def test_detect_browser_phrases():
    phrases = [
        "ouvre chrome",
        "ouvre google chrome",
        "ouvre le navigateur",
        "ouvre mon navigateur",
        "lance chrome",
        "lance google chrome",
        "démarre chrome",
        "demarre chrome",
        "démarre le navigateur",
        "ouvre internet",
        "open chrome",
        "open browser",
        "browser",
        "browser!",
        "launch chrome",
    ]

    for p in phrases:
        intent = detect_intent(p)
        assert intent == "OPEN_BROWSER", f"Phrase '{p}' should map to OPEN_BROWSER, got {intent}"


def test_dispatch_open_browser_calls_tool():
    with patch('core.dispatcher.open_browser') as mock_open:
        mock_open.return_value = "mocked"
        result = dispatcher.dispatch("OPEN_BROWSER")
        mock_open.assert_called_once()
        assert result == "mocked"


def test_detect_spotify_and_terminal_phrases():
    assert detect_intent("ouvre spotify") == "OPEN_SPOTIFY"
    assert detect_intent("lance spotify") == "OPEN_SPOTIFY"
    assert detect_intent("ouvre le terminal") == "OPEN_TERMINAL"
    assert detect_intent("ouvre terminal") == "OPEN_TERMINAL"


def test_dispatch_spotify_calls_tool():
    with patch("core.dispatcher.open_musique", return_value="mocked") as mock_open:
        assert dispatcher.dispatch("OPEN_SPOTIFY") == "mocked"
        mock_open.assert_called_once()
