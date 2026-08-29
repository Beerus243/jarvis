from unittest.mock import patch
from core.environment.actions import ActionType, PlannedAction
from core.environment.execution import ExecutionResult, ExecutionStatus
from core.environment.verification import verify_action

def test_verification_uses_declared_registry_command():
    action=PlannedAction('A1','git',ActionType.VERIFY,'verify git')
    with patch('core.environment.verification.run_command', return_value=ExecutionResult('A1',ExecutionStatus.SUCCESS)) as run:
        result=verify_action(action)
    run.assert_called_once()
    assert result.verification_status == 'SUCCESS'

def test_unknown_verification_is_blocked():
    action=PlannedAction('A1','unknown',ActionType.VERIFY,'verify')
    assert verify_action(action).status == ExecutionStatus.BLOCKED
