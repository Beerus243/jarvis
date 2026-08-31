from types import SimpleNamespace
from core.intent import detect_intent
from core.actions import PCAction, execute_pc_action
from core.actions.screenshot import ScreenCapture

def test_screenshot_intent():
    assert detect_intent("fais une capture d'écran") == "SCREENSHOT"
    assert detect_intent("capture mon écran") == "SCREENSHOT"

def test_unknown_action_blocked():
    result = execute_pc_action(PCAction("RUN_COMMAND"))
    assert not result.success and result.error == "UNKNOWN_ACTION"

def test_capture_success_creates_artifact(tmp_path, monkeypatch):
    target = tmp_path / "screenshot.png"
    def fake_run(*args, **kwargs):
        target.write_bytes(b"png")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/spectacle")
    result = ScreenCapture(tmp_path, runner=fake_run).capture()
    assert result.success and target.exists()

def test_capture_failure_is_structured(tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    result = ScreenCapture(tmp_path).capture()
    assert not result.success and result.error == "SCREENSHOT_UNAVAILABLE"
