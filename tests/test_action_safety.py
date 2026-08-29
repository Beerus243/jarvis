from unittest.mock import patch

from core.environment.action_planner import plan_environment_setup


def test_planner_never_executes_commands():
    env = {"commands": {"flutter": {"status": "ABSENT"}}, "applications": {}, "android": {}}
    with patch("subprocess.run", side_effect=AssertionError("execution forbidden")):
        plan = plan_environment_setup("Flutter", env)
    assert plan.actions
    assert all("subprocess" not in str(action.metadata).lower() for action in plan.actions)


def test_unknown_requirement_becomes_blocked_manual_action():
    env = {"commands": {"flutter": {"status": "UNKNOWN"}}, "applications": {}, "android": {"android_sdk": {"status": "UNKNOWN"}}}
    plan = plan_environment_setup("Flutter", env)
    assert plan.blocked is True
    assert any(action.action_type.value == "MANUAL" for action in plan.actions)
