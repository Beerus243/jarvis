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


def test_confirmation_after_pause_and_rejection_are_local():
    clear_pending()
    with patch("core.brain.add_message"), patch("core.orchestrator._ai_fallback", side_effect=AssertionError("Groq appelé")):
        think("j'ai sommeil")
        think("pause")
        assert "rien" in think("oui").lower()
        think("j'ai sommeil")
        think("pause")
        assert "laisse" in think("non").lower()


def test_explicit_break_is_local_and_confirmable():
    clear_pending()
    with patch("core.brain.add_message"), patch("core.orchestrator._ai_fallback", side_effect=AssertionError("Groq appelé")):
        assert "session" in think("je vais faire une pause").lower()
        assert "session" in think("oui").lower()


def test_continue_uses_known_personality_action_without_inventing_task():
    clear_pending()
    from personality.personality import PersonalityEngine
    engine = PersonalityEngine()
    engine.state.last_action = "je vais relancer les tests"
    response = engine.respond("continue", context={"user_state": {"state": "tired_followup", "answer": "continue"}})
    assert "relancer les tests" in response


def test_break_does_not_claim_to_close_unknown_apps():
    clear_pending()
    from personality.personality import PersonalityEngine
    engine = PersonalityEngine()
    response = engine.respond("pause", context={"user_state": {"state": "tired_followup", "answer": "pause"}, "pc_context": {"applications": []}})
    assert "fermer automatiquement" in response


def test_pause_reports_detected_but_uncontrollable_application():
    clear_pending()
    from personality.personality import PersonalityEngine
    engine = PersonalityEngine()
    response = engine.respond(
        "pause",
        context={
            "user_state": {"state": "tired_followup", "answer": "pause"},
            "pc_context": {"applications": [{
                "name": "VS Code", "running": True,
                "pid": 3086, "controllable": False,
                "capabilities": ["open"],
            }]},
        },
    )
    assert "VS Code" in response
    assert "fermer automatiquement" in response


def test_pause_uses_reliable_active_window_without_closing_it():
    clear_pending()
    from personality.personality import PersonalityEngine
    engine = PersonalityEngine()
    response = engine.respond(
        "pause",
        context={
            "user_state": {"state": "tired_followup", "answer": "pause"},
            "pc_context": {"active_window": {
                "available": True, "application": "VS Code", "title": "brain.py",
                "pid": 3086, "active": True, "closeable": False,
            }},
        },
    )
    assert "VS Code" in response
    assert "fermer" in response.lower()
