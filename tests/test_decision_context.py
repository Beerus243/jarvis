from unittest.mock import patch

from core.decision_context import build_decision_context


def test_empty_context():
    with patch("core.decision_context.load_conversation_context", return_value=[]):
        context = build_decision_context("bonjour")
    assert context["history"] == []
    assert context["previous_user_message"] is None
    assert context["previous_assistant_message"] is None


def test_context_keeps_last_user_and_assistant():
    history = [
        {"role": "user", "message": "ancienne question"},
        {"role": "assistant", "message": "ancienne réponse"},
    ]
    with patch("core.decision_context.load_conversation_context", return_value=history):
        context = build_decision_context("et le serveur ?")
    assert context["previous_user_message"] == "ancienne question"
    assert context["previous_assistant_message"] == "ancienne réponse"
    assert context["message"] == "et le serveur ?"
