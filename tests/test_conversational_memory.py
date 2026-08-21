from unittest.mock import patch

from core.intelligence import analyze
from core.orchestrator import process


def test_project_follow_up_is_contextual_and_local():
    decision = analyze(
        "et le serveur ?",
        context={"previous_user_message": "Quelle technologie utilise mon interface ?"},
    )
    assert decision["type"] == "PROJECT_MEMORY"
    assert decision["uses_context"] is True


def test_why_after_project_question_uses_context():
    decision = analyze(
        "Pourquoi ?",
        context={"previous_user_message": "Quelle technologie utilise mon serveur ?"},
    )
    assert decision["type"] == "CONTEXT"
    assert decision["uses_context"] is True


def test_why_after_personal_question_does_not_invent_reason():
    decision = analyze(
        "Pourquoi ?",
        context={"previous_user_message": "Quelle est ma couleur préférée ?"},
    )
    assert decision["type"] == "CONTEXT"
    with patch("core.orchestrator.build_decision_context", return_value={
        "reference": "Pourquoi ?",
        "reference_info": {},
        "previous_user_message": "Quelle est ma couleur préférée ?",
    }), patch("core.orchestrator._semantic_fallback", return_value=None), \
            patch("core.orchestrator._ai_fallback", return_value="Je n'ai pas cette information.") as ai:
        assert process("Pourquoi ?") == "Je n'ai pas cette information."
        ai.assert_called_once()


def test_complete_question_is_not_replaced_by_context():
    decision = analyze(
        "Quelle technologie utilise mon serveur ?",
        context={"previous_user_message": "Quelle technologie utilise mon interface ?"},
    )
    assert decision["type"] == "PROJECT_MEMORY"
    assert decision["uses_context"] is False


def test_independent_time_question_remains_action():
    decision = analyze("Quelle heure est-il ?", context={
        "previous_user_message": "Pourquoi Python est-il populaire ?"
    })
    assert decision["type"] == "ACTION"


def test_why_without_context_has_no_confident_subject():
    decision = analyze("Pourquoi ?", context={})
    assert decision["type"] == "GENERAL_AI"
    assert decision["confidence"] == 0.50
