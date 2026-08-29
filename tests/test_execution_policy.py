from core.environment.actions import PlannedAction,ActionType,RiskLevel
from core.environment.execution_policy import evaluate_action
def test_policy_confirmation_and_block():
    assert evaluate_action(PlannedAction('1','x',ActionType.INSTALL,'x',risk_level=RiskLevel.MEDIUM,requires_confirmation=True))[0].value=='WAITING_CONFIRMATION'
    assert evaluate_action(PlannedAction('1','x',ActionType.VERIFY,'x',risk_level=RiskLevel.HIGH))[0].value=='BLOCKED'
