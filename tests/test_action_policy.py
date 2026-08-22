import json
from unittest.mock import patch

from core.action_executor import execute_action
from core.action_policy import BLOCKED_ACTION, CONFIRMATION_REQUIRED, SAFE_ACTION, classify_action


def test_safe_action_executes_and_logs(tmp_path, monkeypatch):
    path = tmp_path / "user.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("core.action_executor.MEMORY_FILE", path)
    with patch("core.action_executor.dispatch", return_value="Navigateur ouvert"):
        result = execute_action("OPEN_BROWSER")
    assert result.success is True
    assert result.policy == SAFE_ACTION
    assert json.loads(path.read_text())["action_history"][-1]["action"] == "OPEN_BROWSER"


def test_confirmation_action_is_not_executed_without_confirmation():
    with patch("core.action_executor.dispatch") as dispatch:
        result = execute_action("CLOSE_APPLICATION")
    assert result.success is False
    assert result.policy == CONFIRMATION_REQUIRED
    dispatch.assert_not_called()


def test_blocked_action_is_never_executed():
    with patch("core.action_executor.dispatch") as dispatch:
        result = execute_action("DELETE_FILE", confirmation=True)
    assert result.success is False
    assert result.policy == BLOCKED_ACTION
    dispatch.assert_not_called()


def test_action_failure_is_structured(tmp_path, monkeypatch):
    path = tmp_path / "user.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("core.action_executor.MEMORY_FILE", path)
    with patch("core.action_executor.dispatch", side_effect=RuntimeError("offline")):
        result = execute_action("OPEN_BROWSER")
    assert result.success is False
    assert result.error == "offline"


def test_policy_classification():
    assert classify_action("OPEN_BROWSER") == SAFE_ACTION
    assert classify_action("RUN_COMMAND") == CONFIRMATION_REQUIRED
    assert classify_action("UNKNOWN") == BLOCKED_ACTION
