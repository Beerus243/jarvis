"""Les routes PC atteignent leur exécuteur sans agir sur le système réel."""
from unittest.mock import Mock

import pytest

from core.actions import PCAction
from core.actions import executor
from core.dispatcher import dispatch


@pytest.mark.parametrize("action,parameters,command", [
    ("VOLUME_SET", {"value": "50"}, ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "50%"]),
    ("VOLUME_UNMUTE", {}, ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"]),
    ("MEDIA_STATUS", {}, ["playerctl", "status"]),
])
def test_specific_audio_routes_reach_system_runner(monkeypatch, action, parameters, command):
    run = Mock(return_value=(True, "ok", None))
    monkeypatch.setattr(executor, "run", run)
    result = dispatch({"action": action, **parameters})
    assert result.success
    run.assert_called_once_with(command)


def test_volume_status_reaches_status_handler(monkeypatch):
    status = Mock(return_value=(True, "50%", None))
    monkeypatch.setattr(executor, "volume_status", status)
    assert dispatch({"action": "VOLUME_STATUS"}).message == "50%"
    status.assert_called_once()


def test_structured_folder_reaches_file_handler(monkeypatch, tmp_path):
    monkeypatch.setattr(executor.Path, "home", lambda: tmp_path)
    folder = tmp_path / "Documents"
    folder.mkdir()
    spawn = Mock()
    monkeypatch.setattr(executor.subprocess, "Popen", spawn)
    assert dispatch({"action": "OPEN_FOLDER", "path": str(folder)}).success
    spawn.assert_called_once_with(["xdg-open", str(folder)])


def test_invalid_volume_does_not_execute(monkeypatch):
    run = Mock()
    monkeypatch.setattr(executor, "run", run)
    result = executor.execute_pc_action(PCAction("VOLUME_SET", {"value": "101"}))
    assert not result.success
    run.assert_not_called()
