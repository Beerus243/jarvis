from unittest.mock import patch

from core.response_executor import execute


def test_execute_action():
    with patch("core.response_executor.dispatch", return_value="Ouvert") as dispatch:
        assert execute({"source": "ACTION", "intent": "OPEN_BROWSER"}, "ouvre chrome") == "Ouvert"
        dispatch.assert_called_once_with("OPEN_BROWSER")


def test_execute_personal_memory():
    with patch("core.response_executor.answer_personal_question", return_value="Jaune") as answer:
        assert execute({"source": "PERSONAL_MEMORY"}, "ma couleur") == "Jaune"
        answer.assert_called_once()


def test_execute_project_memory():
    with patch("core.response_executor.answer_project_question", return_value="FastAPI") as answer:
        result = execute(
            {"source": "PROJECT_MEMORY"},
            "et le serveur ?",
            {"reference_info": {"query": "quelle technologie gère mon serveur"}},
        )
        assert result == "FastAPI"
        answer.assert_called_once()


def test_execute_context():
    with patch("core.response_executor.answer_project_question", return_value="React") as answer:
        assert execute(
            {"source": "CONTEXT"}, "et le frontend ?",
            {"reference_info": {"query": "quelle technologie utilise mon interface"}},
        ) == "React"
        answer.assert_called_once()


def test_execute_clarification_does_not_call_external_sources():
    with patch("core.response_executor.dispatch") as dispatch, \
            patch("core.response_executor.answer_personal_question") as personal:
        result = execute({"source": "CLARIFICATION"}, "et lui ?")
        assert "préciser" in result
        dispatch.assert_not_called()
        personal.assert_not_called()


def test_execute_semantic_memory():
    with patch("core.response_executor._semantic_search", return_value={"contenu": "souvenir"}) as search:
        assert execute({"source": "SEMANTIC_MEMORY"}, "question") == "souvenir"
        search.assert_called_once()


def test_execute_ai():
    with patch("core.response_executor._ask_ai", return_value="réponse IA") as ask:
        assert execute({"source": "AI"}, "pourquoi ?") == "réponse IA"
        ask.assert_called_once()


def test_local_executor_never_falls_through_to_semantic_or_ai():
    with patch("core.response_executor.answer_personal_question", return_value="local"), \
            patch("core.response_executor.dispatch") as dispatch, \
            patch("core.response_executor._semantic_search") as semantic, \
            patch("core.response_executor._ask_ai") as ai:
        assert execute({"source": "PERSONAL_MEMORY"}, "qui suis-je") == "local"
        dispatch.assert_not_called()
        semantic.assert_not_called()
        ai.assert_not_called()
