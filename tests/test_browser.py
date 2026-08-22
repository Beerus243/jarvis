from unittest.mock import patch

from core.action_parser import parse_actions
from tools.browser import open_url, search_web, search_wikipedia


def test_open_url():
    with patch("tools.browser.subprocess.Popen") as popen:
        ok, _ = open_url("https://www.youtube.com")
    assert ok is True
    popen.assert_called_once()


def test_search_web():
    with patch("tools.browser.subprocess.Popen") as popen:
        search_web("Python avancé")
    assert "Python%20avanc%C3%A9" in popen.call_args.args[0][1]


def test_search_wikipedia():
    with patch("tools.browser.subprocess.Popen") as popen:
        search_wikipedia("Thor")
    assert "Thor" in popen.call_args.args[0][1]


def test_wikipedia_query_extraction():
    assert parse_actions("cherche Thor sur Wikipédia")[0] == {"action": "SEARCH_WIKIPEDIA", "query": "thor"}


def test_navigation_intents():
    assert parse_actions("va sur Wikipédia")[0]["action"] == "OPEN_URL"
    assert parse_actions("cherche Python")[0]["action"] == "SEARCH_WEB"
