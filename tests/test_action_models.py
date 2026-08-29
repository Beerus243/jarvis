from core.environment.actions import ActionType, ExecutionPlan, PlannedAction, RiskLevel


def test_action_models_serialize_enums():
    action = PlannedAction("A001", "flutter", ActionType.INSTALL, "Install Flutter",
                           risk_level=RiskLevel.MEDIUM, requires_confirmation=True)
    plan = ExecutionPlan("flutter_development", "Flutter", [action])
    assert plan.to_dict()["actions"][0]["action_type"] == "INSTALL"
    assert plan.to_dict()["requires_confirmation"] is True
