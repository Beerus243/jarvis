from unittest.mock import patch

from core.environment.requirement_resolver import format_requirement_plan, resolve_requirements


def test_resolver_inspects_only_when_snapshot_missing():
    with patch("core.environment.requirement_resolver.inspect_environment", return_value={"commands": {}, "applications": {}, "android": {}}) as inspect:
        resolve_requirements("Flutter")
        inspect.assert_called_once_with()


def test_supplied_environment_is_not_modified():
    snapshot = {"commands": {}, "applications": {}, "android": {}}
    before = repr(snapshot)
    resolve_requirements("Flutter", snapshot)
    assert repr(snapshot) == before


def test_action_order_is_deterministic_and_read_only():
    snapshot = {"commands": {name: {"status": "ABSENT"} for name in ("flutter", "dart", "java", "javac", "adb", "git")},
                "applications": {}, "android": {"android_sdk": {"status": "ABSENT"}}}
    plan = resolve_requirements("Flutter", snapshot)
    assert [item["requirement"] for item in plan.actions][:3] == ["javac", "adb", "flutter"]
    assert "aucune action" in format_requirement_plan(plan).lower()


def test_unknown_component_is_not_reported_as_missing():
    snapshot = {"commands": {name: {"status": "UNKNOWN"} for name in ("flutter", "dart", "java", "javac", "adb", "git")},
                "applications": {}, "android": {"android_sdk": {"status": "UNKNOWN"}}}
    plan = resolve_requirements("Flutter", snapshot)
    assert all(item.status.value == "UNKNOWN" for item in plan.requirements)
