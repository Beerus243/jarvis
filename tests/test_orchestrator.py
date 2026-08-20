from unittest.mock import patch

from core.orchestrator import process


def test_action():
    with patch("core.orchestrator.dispatch", return_value="Navigateur ouvert") as dispatch:
        assert process("ouvre mon navigateur") == "Navigateur ouvert"
        dispatch.assert_called_once_with("OPEN_BROWSER")


def test_personal_memory():
    with patch("core.orchestrator.answer_personal_question", return_value="Tu es Fabrice."):
        with patch("core.orchestrator._semantic_fallback") as semantic:
            assert process("qui suis-je") == "Tu es Fabrice."
            semantic.assert_not_called()


def test_project_memory():
    with patch("core.orchestrator.answer_project_question", return_value="Le frontend utilise React."):
        assert process("quelle technologie utilise mon interface") == "Le frontend utilise React."


def test_general_ai_fallback():
    with patch("core.orchestrator._semantic_fallback", return_value=None), \
            patch("core.orchestrator._ai_fallback", return_value="Réponse IA") as ai:
        assert process("pourquoi Python est populaire ?") == "Réponse IA"
        ai.assert_called_once()


def test_personal_memory_precedes_semantic_memory():
    with patch("core.orchestrator.answer_personal_question", return_value="Ta couleur préférée est jaune.") as personal, \
            patch("core.orchestrator._semantic_fallback") as semantic, \
            patch("core.orchestrator._ai_fallback") as ai:
        assert process("quelle est ma couleur préférée")
        personal.assert_called_once()
        semantic.assert_not_called()
        ai.assert_not_called()


def test_project_follow_up_keeps_local_priority():
    with patch("core.orchestrator.answer_project_question", return_value="Le backend utilise FastAPI.") as project, \
            patch("core.orchestrator._semantic_fallback") as semantic:
        assert process("et le serveur ?") == "Le backend utilise FastAPI."
        project.assert_called_once()
        semantic.assert_not_called()
