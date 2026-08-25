from unittest.mock import patch

from core.action_parser import parse_actions
from core.brain import think
from core.intelligence import analyze
from personality.personality import clear_pending, get_pending_context


def test_incomplete_music_request_is_clarification():
    action = parse_actions("mets-moi une musique")[0]
    assert action["action"] == "PLAY_MUSIC"
    assert "artist" not in action and "title" not in action
    assert analyze("mets-moi une musique")["type"] == "CLARIFICATION"


def test_music_followup_keeps_pending_intent():
    clear_pending()
    with patch("core.brain.add_message"), patch("core.orchestrator.dispatch", return_value=(True, "Je lance Damso.")):
        assert "précis" in think("mets-moi une musique")
        assert get_pending_context()["intent"] == "PLAY_MUSIC"
        assert think("Damso") == "Je lance Damso."
    assert get_pending_context() is None


def test_fatigue_followups_are_local():
    clear_pending()
    with patch("core.brain.add_message"), patch("core.orchestrator._ai_fallback", side_effect=AssertionError("Groq appelé")):
        think("j'ai sommeil")
        assert "pause" in think("pause").lower()
