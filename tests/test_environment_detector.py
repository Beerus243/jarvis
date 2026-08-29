import subprocess

from core.environment.commands import detect_command, detect_package_managers
from core.environment.detector import inspect_android, inspect_applications


def fake_runner(*args, **kwargs):
    return subprocess.CompletedProcess(args[0], 0, stdout="tool 1.2\n", stderr="")


def test_existing_command_and_version():
    result = detect_command("tool", which=lambda _: "/usr/bin/tool", runner=fake_runner)
    assert result.status == "PRESENT"
    assert result.version == "tool 1.2"


def test_absent_command():
    result = detect_command("missing", which=lambda _: None, runner=fake_runner)
    assert result.status == "ABSENT"


def test_package_manager_selection():
    result = detect_package_managers(which=lambda name: "/usr/bin/dnf" if name == "dnf" else None,
                                     runner=fake_runner)
    assert result["selected"]["name"] == "dnf"


def test_applications_are_detected_without_duplicate_catalogue():
    result = inspect_applications(which=lambda name: "/usr/bin/code" if name == "code" else None)
    assert result["vscode"]["status"] == "PRESENT"
    assert result["spotify"]["status"] == "ABSENT"


def test_android_absent_is_safe(monkeypatch, tmp_path):
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path / "missing"))
    monkeypatch.setattr("core.environment.detector.Path.home", lambda: tmp_path)
    result = inspect_android(which=lambda _: None)
    assert result["android_sdk"]["status"] == "ABSENT"
