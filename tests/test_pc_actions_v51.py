from types import SimpleNamespace
from core.intent import detect_intent
from core.actions import PCAction, execute_pc_action
from core.actions.screenshot import ScreenCapture
from core.dispatcher import dispatch

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

def test_dispatcher_propagates_screenshot_result(monkeypatch):
    expected = SimpleNamespace(success=True, message="Capture d'écran effectuée.", error=None, artifact_path="/tmp/test.png")
    monkeypatch.setattr("core.dispatcher.execute_pc_action", lambda action: expected)
    assert dispatch("SCREENSHOT") is expected
from pathlib import Path
from unittest.mock import patch
from core.actions import PCAction
from core.actions.executor import execute_pc_action
from core.action_executor import execute_action
from core.action_policy import CONFIRMATION_REQUIRED
from core.intent import detect_intent

def test_v58_application_intent_is_structured():
    assert detect_intent("ouvre Firefox") == {"action": "OPEN_APPLICATION", "target": "firefox"}

@patch("core.actions.executor.open_application", return_value=(True, "ouvert"))
def test_v58_open_application_action(mock_open):
    result = execute_pc_action(PCAction("OPEN_APPLICATION", {"application": "firefox"}))
    assert result.success is True
    mock_open.assert_called_once_with("firefox")

def test_v58_close_application_requires_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr("core.action_executor.MEMORY_FILE", tmp_path / "user.json")
    result = execute_action({"action": "CLOSE_APPLICATION", "target": "firefox"})
    assert result.policy == CONFIRMATION_REQUIRED
    assert result.success is False

@patch("core.actions.executor.open_url", return_value=(True, "ouvert"))
def test_v58_open_url_action(mock_open):
    result = execute_pc_action(PCAction("OPEN_URL", {"url": "https://www.google.com"}))
    assert result.success is True

def test_v58_file_copy_stays_inside_home(tmp_path):
    source = tmp_path / "a.txt"; target = tmp_path / "b.txt"; source.write_text("ok")
    with patch("core.actions.executor.Path.home", return_value=tmp_path):
        result = execute_pc_action(PCAction("FILE_COPY", {"source": str(source), "target": str(target)}))
    assert result.success is True and target.read_text() == "ok"

@patch("core.actions.executor.shutil.which", return_value=None)
def test_v58_media_action_reports_not_supported(_):
    result = execute_pc_action(PCAction("MEDIA_NEXT"))
    assert result.success is False and result.error == "NOT_SUPPORTED"

def test_v58_unknown_pc_action_blocked():
    assert execute_pc_action(PCAction("RAW_COMMAND", {"command": "rm -rf /"})).success is False

def test_v59_natural_pc_parsing():
    assert detect_intent("Hey Jarvis, ouvre YouTube") == {"action": "OPEN_URL", "url": "https://www.youtube.com"}
    assert detect_intent("ouvre le dossier Jarvis") == {"action": "OPEN_FOLDER", "path": "jarvis"}
    assert detect_intent("crée-moi un fichier au nom de rapport.txt") == {"action": "FILE_CREATE", "path": "rapport.txt"}
    assert detect_intent("ouvre le fichier test.txt") == {"action": "FILE_OPEN", "path": "test.txt"}

def test_v59_unsafe_file_paths_are_rejected(tmp_path):
    with patch("core.actions.executor.Path.home", return_value=tmp_path):
        result = execute_pc_action(PCAction("FILE_OPEN", {"path": "/etc/passwd"}))
    assert result.success is False

@patch("core.actions.executor.subprocess.Popen")
def test_v59_open_folder_does_not_create_missing_folder(mock_popen, tmp_path):
    with patch("core.actions.executor.Path.home", return_value=tmp_path):
        result = execute_pc_action(PCAction("OPEN_FOLDER", {"path": "Missing"}))
    assert not result.success
    mock_popen.assert_not_called()

def test_v510_missing_file_name_requests_clarification():
    assert detect_intent("crée un fichier") == {"action": "FILE_CREATE", "needs_clarification": True}
