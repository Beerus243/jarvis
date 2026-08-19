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
