from core.environment.action_planner import plan_environment_setup


def test_dependencies_reference_existing_actions_and_are_topological():
    env = {"commands": {name: {"status": "ABSENT"} for name in ("flutter", "dart", "java", "javac", "adb", "git")},
           "applications": {}, "android": {"android_sdk": {"status": "ABSENT"}}}
    actions = plan_environment_setup("Flutter", env).actions
    positions = {a.id: i for i, a in enumerate(actions)}
    assert all(dep in positions and positions[dep] < positions[action.id] for action in actions for dep in action.dependencies)
