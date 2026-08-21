from core.execution_result import ExecutionResult


def test_success_result():
    result = ExecutionResult(True, "ACTION", response="ok")
    assert result.success is True
    assert result.response == "ok"


def test_failure_result():
    result = ExecutionResult(False, "AI", error="offline")
    assert result.success is False
    assert result.error == "offline"


def test_default_values():
    result = ExecutionResult(True, "PROJECT_MEMORY")
    assert result.response is None
    assert result.error is None
    assert result.fallback_allowed is False
