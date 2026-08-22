from core.command_understanding import normalize_command, resolve_command_terms
from core.action_parser import parse_actions
from core.intent import detect_intent


def test_normalization_and_aliases():
    assert normalize_command("Peux-tu ouvrir Spotify ?") == "peux tu ouvrir spotify"
    assert "spotify" in resolve_command_terms("ouvre spofity")["aliases"]


def test_typo_commands():
    assert detect_intent("ouvre spotfy") == "OPEN_SPOTIFY"
    assert detect_intent("ouvre le navgateur") == "OPEN_BROWSER"
    assert parse_actions("cherche Thor sur wikipdia")[0]["action"] == "SEARCH_WIKIPEDIA"


def test_media_and_false_positive():
    assert parse_actions("met moi du damso")[0]["action"] == "PLAY_MUSIC"
    assert detect_intent("pourquoi spotify existe") is None
