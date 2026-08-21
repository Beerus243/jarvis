from core.response_planner import plan


def test_action_plan():
    assert plan({"type": "ACTION", "confidence": 0.98})["source"] == "ACTION"


def test_personal_memory_plan():
    result = plan({"type": "PERSONAL_MEMORY", "confidence": 0.99})
    assert result["source"] == "PERSONAL_MEMORY"
    assert result["requires_ai"] is False


def test_project_memory_plan():
    assert plan({"type": "PROJECT_MEMORY", "confidence": 0.95})["source"] == "PROJECT_MEMORY"


def test_context_plan():
    assert plan({"type": "CONTEXT", "confidence": 0.85})["source"] == "CONTEXT"


def test_general_ai_plan():
    result = plan({"type": "GENERAL_AI", "confidence": 0.50, "requires_ai": True})
    assert result["source"] == "AI"
    assert result["requires_ai"] is True


def test_low_confidence_uses_fallback():
    result = plan({"type": "PERSONAL_MEMORY", "confidence": 0.30, "requires_memory": True})
    assert result["source"] == "SEMANTIC_MEMORY"


def test_ambiguous_context_requires_clarification():
    result = plan({"type": "CONTEXT", "confidence": 0.35, "ambiguous": True})
    assert result["source"] == "CLARIFICATION"
    assert result["ambiguous"] is True


def test_unknown_decision_is_safe():
    result = plan({"type": "UNKNOWN", "confidence": 0.1})
    assert result["source"] == "CLARIFICATION"
