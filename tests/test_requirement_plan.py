from core.environment.requirement_resolver import format_requirement_plan, resolve_requirements


def test_plan_formatter_exposes_gaps_and_statuses():
    plan = resolve_requirements("Je veux développer une application Flutter", {
        "commands": {"flutter": {"status": "ABSENT"}}, "applications": {},
        "android": {"android_sdk": {"status": "ABSENT"}},
    })
    text = format_requirement_plan(plan)
    assert "JARVIS ENVIRONMENT ANALYSIS" in text
    assert "Flutter SDK" in text
    assert "MISSING" in text
