from unittest.mock import patch

from core.pc_context import get_known_applications


def test_known_application_absent_is_reported_without_pid():
    applications = get_known_applications([])
    vscode = next(item for item in applications if item["name"] == "VS Code")
    assert vscode == {
        "name": "VS Code",
        "running": False,
        "pid": None,
        "controllable": False,
        "capabilities": ["open"],
    }


def test_primary_pid_groups_child_processes():
    processes = [
        {"pid": 3086, "ppid": 1296, "comm": "code"},
        {"pid": 3169, "ppid": 3086, "comm": "code"},
        {"pid": 3258, "ppid": 3086, "comm": "code"},
    ]
    vscode = next(item for item in get_known_applications(processes) if item["name"] == "VS Code")
    assert vscode["running"] is True
    assert vscode["pid"] == 3086
    assert vscode["controllable"] is False


def test_spotify_exposes_only_real_control_capabilities():
    applications = get_known_applications([{"pid": 1234, "ppid": 1, "comm": "spotify"}])
    spotify = next(item for item in applications if item["name"] == "Spotify")
    assert spotify["running"] is True
    assert spotify["pid"] == 1234
    assert spotify["controllable"] is True
    assert "spotify_control" in spotify["capabilities"]
    assert "close" not in spotify["capabilities"]


def test_process_probe_failure_is_safe():
    with patch("core.pc_context.subprocess.run", side_effect=OSError("ps indisponible")):
        assert get_known_applications()[-1]["running"] is False
