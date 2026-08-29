from core.environment.requirement_resolver import resolve_requirements
from core.environment.requirements import RequirementStatus


def env(**statuses):
    commands = {name: {"status": status, "path": f"/usr/bin/{name}"} for name, status in statuses.items()}
    return {"commands": commands, "applications": {}, "android": {"android_sdk": {"status": "ABSENT"}}}


def test_flutter_profile_contains_generic_requirements():
    plan = resolve_requirements("Prépare mon environnement Flutter", env(flutter="PRESENT", dart="PRESENT", java="PRESENT", javac="PRESENT", adb="PRESENT", git="PRESENT"))
    names = {item.name for item in plan.requirements}
    assert {"flutter", "dart", "java", "javac", "android_sdk", "adb", "git"} <= names


def test_java_without_javac_is_misconfigured():
    snapshot = env(flutter="ABSENT", dart="ABSENT", java="PRESENT", javac="ABSENT", adb="ABSENT", git="PRESENT")
    snapshot["android"]["android_sdk"] = {"status": "PRESENT", "path": "/sdk", "adb": "/sdk/platform-tools/adb"}
    plan = resolve_requirements("développement Flutter", snapshot)
    assert next(r for r in plan.requirements if r.name == "javac").status == RequirementStatus.MISCONFIGURED
    assert next(r for r in plan.requirements if r.name == "adb").status == RequirementStatus.MISCONFIGURED


def test_complete_environment_has_no_required_gaps():
    snapshot = env(flutter="PRESENT", dart="PRESENT", java="PRESENT", javac="PRESENT", adb="PRESENT", git="PRESENT")
    snapshot["android"] = {"android_sdk": {"status": "PRESENT", "path": "/sdk"}, "android_studio": {"status": "PRESENT"}}
    plan = resolve_requirements("application Flutter", snapshot)
    assert plan.gaps == []


def test_unknown_request_is_explicit():
    plan = resolve_requirements("ouvre Spotify", environment={})
    assert plan.profile is None
    assert plan.actions == []
