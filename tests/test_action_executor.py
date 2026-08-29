from core.environment.actions import PlannedAction,ActionType
from core.environment.action_executor import execute_action
def test_verify_action_runs_through_registry():
    a=PlannedAction('A1','git',ActionType.VERIFY,'verify')
    assert execute_action(a).status.value=='SUCCESS'
