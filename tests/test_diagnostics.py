import logging

from core.diagnostics import (
    DiagnosticEvent,
    clear_diagnostics,
    format_diagnostic,
    get_last_diagnostics,
)
from core.orchestrator import process


def setup_function():
    clear_diagnostics()


def test_event_creation_and_formatting():
    event = DiagnosticEvent("PLANNER", source="PERSONAL_MEMORY", confidence=0.98, success=True)
    text = format_diagnostic(event)
    assert "[PLANNER]" in text
    assert "source=PERSONAL_MEMORY" in text
    assert "confidence=0.98" in text
    assert "success=True" in text


def test_local_request_records_pipeline():
    assert process("bonjour")
    assert [event.stage for event in get_last_diagnostics()] == [
        "INTELLIGENCE", "PLANNER", "EXECUTOR"
    ]


def test_personal_memory_is_traced_locally():
    from unittest.mock import patch

    with patch("core.orchestrator.answer_personal_question", return_value="jaune"):
        assert process("quelle est ma couleur préférée") == "jaune"
    events = get_last_diagnostics()
    assert events[0].source == "PERSONAL_MEMORY"
    assert events[1].source == "PERSONAL_MEMORY"
    assert all(event.source != "AI" for event in events)


def test_project_memory_is_traced_locally():
    from unittest.mock import patch

    with patch("core.orchestrator.answer_project_question", return_value="React"):
        assert process("quelle technologie utilise mon interface") == "React"
    assert get_last_diagnostics()[0].source == "PROJECT_MEMORY"


def test_ai_trace_is_mocked():
    from unittest.mock import patch

    with patch("core.orchestrator.build_decision_context", return_value={
        "reference": "Pourquoi Python est populaire ?",
        "reference_info": {},
        "previous_user_message": None,
    }), patch("core.orchestrator._ai_fallback", return_value="réponse IA"):
        assert process("Pourquoi Python est populaire ?") == "réponse IA"
    assert get_last_diagnostics()[1].source == "AI"


def test_debug_is_silent_by_default(capsys):
    process("bonjour")
    assert capsys.readouterr().out == ""


def test_debug_logs_events(monkeypatch, caplog):
    monkeypatch.setenv("JARVIS_DEBUG", "1")
    with caplog.at_level(logging.INFO, logger="jarvis.diagnostics"):
        process("bonjour")
    assert "[INTELLIGENCE]" in caplog.text
    assert "[PLANNER]" in caplog.text
    assert "[EXECUTOR]" in caplog.text
