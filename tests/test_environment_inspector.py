from core.environment.inspector import format_environment_report


def test_report_formatting():
    report = format_environment_report({
        "system": {"distribution": "Fedora", "kernel": "6", "architecture": "x86_64",
                    "hostname": "host", "user": "fabrice", "cwd": "/tmp"},
        "commands": {"git": {"status": "PRESENT", "version": "git 2"}},
        "applications": {"vscode": {"status": "PRESENT"}},
        "android": {"android_sdk": {"status": "ABSENT"}, "android_studio": {"status": "ABSENT"}},
    })
    assert "Fedora" in report
    assert "git" in report
    assert "Aucune installation" in report


def test_environment_result_has_expected_sections(monkeypatch):
    import core.environment.inspector as inspector
    monkeypatch.setattr(inspector, "detect_command", lambda name: type("C", (), {"to_dict": lambda self: {"name": name, "status": "ABSENT"}})())
    monkeypatch.setattr(inspector, "detect_package_managers", lambda: {"selected": None, "available": []})
    monkeypatch.setattr(inspector, "inspect_system", lambda: {})
    monkeypatch.setattr(inspector, "inspect_applications", lambda: {})
    monkeypatch.setattr(inspector, "inspect_flutter", lambda _: {})
    monkeypatch.setattr(inspector, "inspect_android", lambda: {})
    monkeypatch.setattr(inspector, "inspect_gpu", lambda: {})
    monkeypatch.setattr(inspector, "inspect_network", lambda: {})
    monkeypatch.setattr(inspector, "inspect_storage", lambda: {})
    from core.environment.inspector import inspect_environment
    result = inspect_environment()
    assert {"system", "package_manager", "commands", "applications", "flutter", "java", "android", "environment", "gpu", "network", "storage"} <= result.keys()
