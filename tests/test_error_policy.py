from unittest.mock import patch

from core.execution_result import ExecutionResult
from core.response_executor import execute
from core.orchestrator import process


def test_personal_memory_found_is_not_recoverable():
    with patch("core.response_executor.answer_personal_question", return_value="jaune"):
        result = execute({"source": "PERSONAL_MEMORY"}, "couleur")
    assert result.success is True
    assert result.fallback_allowed is False
    assert result.error_type == "NONE"


def test_personal_memory_missing_is_not_sent_to_groq():
    with patch("core.response_executor.answer_personal_question", return_value=None):
        result = execute({"source": "PERSONAL_MEMORY"}, "couleur")
    assert result.success is False
    assert result.error_type == "NOT_FOUND"
    assert result.fallback_allowed is False


def test_personal_process_never_calls_ai_when_missing():
    with patch("core.orchestrator.answer_personal_question", return_value=None), \
            patch("core.orchestrator._ai_fallback") as ai:
        assert process("quelle est ma couleur préférée") is None
    ai.assert_not_called()


def test_project_memory_missing_is_not_recoverable():
    with patch("core.response_executor.answer_project_question", return_value=None):
        result = execute({"source": "PROJECT_MEMORY"}, "frontend")
    assert result.error_type == "NOT_FOUND"
    assert result.fallback_allowed is False


def test_ambiguous_context_is_local_and_nonrecoverable():
    result = execute({"source": "CONTEXT", "ambiguous": True}, "et lui ?")
    assert result.success is False
    assert result.error_type == "AMBIGUOUS"
    assert result.fallback_allowed is False


def test_semantic_memory_found():
    with patch("core.response_executor._semantic_search", return_value={"contenu": "souvenir"}):
        result = execute({"source": "SEMANTIC_MEMORY"}, "question")
    assert result.success is True
    assert result.error_type == "NONE"


def test_semantic_memory_missing_allows_ai_fallback():
    with patch("core.response_executor._semantic_search", return_value=None):
        result = execute({"source": "SEMANTIC_MEMORY"}, "question")
    assert result.success is False
    assert result.error_type == "NOT_FOUND"
    assert result.fallback_allowed is True


def test_internal_error_never_falls_through_to_groq():
    with patch("core.response_executor.answer_project_question", side_effect=RuntimeError("broken")):
        result = execute({"source": "PROJECT_MEMORY"}, "frontend")
    assert result.success is False
    assert result.error_type == "INTERNAL_ERROR"
    assert result.fallback_allowed is False


def test_action_success_has_no_fallback():
    with patch("core.response_executor.dispatch", return_value="ok"):
        result = execute({"source": "ACTION", "intent": "GET_TIME"}, "heure")
    assert result.success is True
    assert result.fallback_allowed is False


def test_action_error_is_recoverable():
    with patch("core.response_executor.dispatch", return_value=None):
        result = execute({"source": "ACTION", "intent": "UNKNOWN"}, "action")
    assert result.success is False
    assert result.error_type == "NOT_FOUND"
    assert result.fallback_allowed is True


def test_ai_error_is_final():
    with patch("core.response_executor._ask_ai", side_effect=RuntimeError("offline")):
        result = execute({"source": "AI"}, "question")
    assert result.success is False
    assert result.error_type == "EXTERNAL_ERROR"
    assert result.fallback_allowed is False


def test_clarification_never_calls_external_source():
    with patch("core.response_executor._semantic_search") as semantic, \
            patch("core.response_executor._ask_ai") as ai:
        result = execute({"source": "CLARIFICATION"}, "et lui ?")
    assert result.success is True
    assert result.error_type == "NONE"
    semantic.assert_not_called()
    ai.assert_not_called()


def test_execution_result_default_error_type():
    assert ExecutionResult(True, "ACTION").error_type == "NONE"
