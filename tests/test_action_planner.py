from core.environment.action_planner import format_execution_plan, plan_actions, plan_environment_setup
from core.environment.requirement_resolver import resolve_requirements


def snapshot(**statuses):
    return {"commands": {name: {"status": value} for name, value in statuses.items()},
            "applications": {}, "android": {"android_sdk": {"status": "PRESENT", "path": "/sdk", "adb": "/sdk/platform-tools/adb"},
                                                "android_studio": {"status": "PRESENT"}}}


def test_current_flutter_gaps_become_abstract_actions_in_dependency_order():
    requirement_plan = resolve_requirements("Flutter", snapshot(flutter="ABSENT", dart="ABSENT", java="PRESENT", javac="ABSENT", adb="ABSENT", git="PRESENT"))
    plan = plan_actions(requirement_plan)
    assert [a.requirement for a in plan.actions] == ["javac", "javac", "adb", "adb", "flutter", "flutter", "dart", "android_toolchain"]
    assert plan.actions[0].action_type.value == "CONFIGURE"
    assert plan.actions[1].dependencies == [plan.actions[0].id]
    assert all(not action.metadata for action in plan.actions)


def test_present_components_are_not_installed():
    plan = plan_environment_setup("Flutter", snapshot(flutter="PRESENT", dart="PRESENT", java="PRESENT", javac="PRESENT", adb="PRESENT", git="PRESENT"))
    assert plan.actions == []


def test_formatter_contains_summary():
    plan = plan_environment_setup("Flutter", snapshot(flutter="ABSENT", dart="ABSENT", java="ABSENT", javac="ABSENT", adb="ABSENT", git="ABSENT"))
    assert "JARVIS ACTION PLAN" in format_execution_plan(plan)
