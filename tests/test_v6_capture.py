"""Captures locales : routage vocal, sélection, propriété et finalisation vidéo."""
import json
from pathlib import Path
import subprocess
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core.capture.commands import parse_capture_command
from core.capture.recording import ScreenRecorder
from core.actions.screenshot import ScreenCapture
from core.actions import PCAction, execute_pc_action
from core.dispatcher import dispatch
from core.intent import detect_intent


@pytest.mark.parametrize('text,expected', [
    ("fais une capture d’écran", 'SCREENSHOT'),
    ('capture mon écran', 'SCREENSHOT'),
    ('Hey Jarvis, capture la fenêtre active', {'action': 'SCREENSHOT', 'scope': 'window'}),
    ('prends une capture de la fenêtre active', {'action': 'SCREENSHOT', 'scope': 'window'}),
    ("capture une zone de l’écran", {'action': 'SCREENSHOT', 'scope': 'region'}),
    ('enregistre mon écran pendant trente secondes', {'action': 'RECORDING_START', 'scope': 'screen', 'duration': 30}),
    ('enregistre la fenêtre pendant deux minutes', {'action': 'RECORDING_START', 'scope': 'window', 'duration': 120}),
    ("fais une capture vidéo de l’écran", {'action': 'RECORDING_START', 'scope': 'screen', 'duration': 60}),
    ('filme une zone pendant 15 secondes', {'action': 'RECORDING_START', 'scope': 'region', 'duration': 15}),
    ('arrête la vidéo', {'action': 'RECORDING_STOP'}),
    ("statut de l’enregistrement", {'action': 'RECORDING_STATUS'}),
])
def test_capture_intents(text, expected):
    assert parse_capture_command(text) == expected
    assert detect_intent(text) == expected


@pytest.mark.parametrize('text', [
    "ne fais pas de capture d’écran", "ne fais une capture d’écran que demain",
    "comment faire une capture d’écran", "explique screenshot", 'ne filme pas mon écran',
    'enregistre mon écran sans arrêt', "enregistre mon écran pendant -5 secondes",
    'surveille cette compilation', 'regarde mon écran', 'arrête la surveillance',
])
def test_capture_does_not_match_other_requests(text):
    assert parse_capture_command(text) is None


@pytest.mark.parametrize('scope,flag', [('screen', '--fullscreen'), ('window', '--activewindow'), ('region', '--region')])
def test_saved_capture_is_unique_and_separate_instance(tmp_path, monkeypatch, scope, flag):
    monkeypatch.setattr('shutil.which', lambda _: '/usr/bin/spectacle')
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        Path(argv[-1]).write_bytes(b'png')
        return SimpleNamespace(returncode=0)
    capture = ScreenCapture(tmp_path, runner=run)
    first, second = capture.capture(scope), capture.capture(scope)
    assert first.success and second.success
    assert first.artifact_path != second.artifact_path
    assert Path(first.artifact_path).read_bytes() == b'png'
    assert flag in calls[0][0] and '--new-instance' in calls[0][0]
    assert calls[0][1]['timeout'] == (60 if scope == 'region' else 20)


def test_old_screenshot_does_not_hide_failure(tmp_path, monkeypatch):
    monkeypatch.setattr('shutil.which', lambda _: 'spectacle')
    (tmp_path / 'screenshot.png').write_bytes(b'old')
    result = ScreenCapture(tmp_path, runner=Mock(return_value=SimpleNamespace(returncode=0))).capture()
    assert not result.success


def test_region_timeout_and_invalid_scope_are_controlled(tmp_path, monkeypatch):
    monkeypatch.setattr('shutil.which', lambda _: 'spectacle')
    runner = Mock(side_effect=subprocess.TimeoutExpired('spectacle', 60))
    capture = ScreenCapture(tmp_path, runner=runner)
    assert capture.capture('region').error == 'CAPTURE_TIMEOUT'
    assert capture.capture('--shell').error == 'INVALID_SCOPE'
    assert runner.call_count == 1


class Process:
    pid = 123
    returncode = None
    terminated = False
    def poll(self):
        return self.returncode
    def wait(self, timeout):
        self.returncode = 0
        return 0
    def terminate(self):
        self.terminated = True
        self.returncode = -15
    def kill(self):
        self.returncode = -9


@pytest.fixture
def recorder(tmp_path, monkeypatch):
    real_thread_start = threading.Thread.start
    monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')
    monkeypatch.setattr('shutil.which', lambda tool: '/usr/bin/' + tool)
    monkeypatch.setattr('threading.Thread.start', lambda _: None)
    process = Process()
    def run(argv, **kwargs):
        if argv[0] == 'ffprobe':
            return SimpleNamespace(returncode=0, stdout=json.dumps({'streams': [{'codec_type': 'video', 'width': 1280, 'height': 720}], 'format': {'duration': '3.0'}}))
        method = argv[argv.index('--method') + 1]
        responses = {'GetNameOwner': "(':1.123',)", 'GetConnectionUnixProcessID': '(uint32 123,)', 'CommandLine': '(0,)'}
        if method.endswith('NameHasOwner'):
            return SimpleNamespace(returncode=0, stdout='(true,)' if rec.process else '(false,)')
        return SimpleNamespace(returncode=0, stdout=responses[method.rsplit('.', 1)[1]])
    rec = ScreenRecorder(tmp_path, runner=Mock(side_effect=run), popen=Mock(return_value=process))
    rec.real_thread_start = real_thread_start
    yield rec
    rec.stop()


def test_recording_finalizes_before_claiming_success(recorder):
    assert recorder.start(duration=30).success
    assert not recorder.start().success
    assert not recorder.status().artifact_path
    recorder.target.write_bytes(b'webm')
    result = recorder.stop()
    assert result.success and Path(result.artifact_path).exists()
    assert not recorder.popen.return_value.terminated
    calls = [c.args[0] for c in recorder.run.call_args_list]
    stop_call = next(c for c in calls if 'org.kde.KDBusService.CommandLine' in c)
    assert stop_call[stop_call.index('--dest') + 1] == ':1.123'
    assert "['spectacle', '--dbus', '--nonotify']" in stop_call
    assert calls[-1][0] == 'ffprobe'


def test_missing_video_never_reports_saved(recorder):
    recorder.start()
    assert not recorder.stop().success


def test_foreign_spectacle_is_never_launched_or_stopped(recorder, monkeypatch):
    monkeypatch.setattr(recorder, '_owner', lambda: ':1.555')
    assert recorder.start().error == 'SPECTACLE_BUSY'
    recorder.popen.assert_not_called()
    assert not recorder.popen.return_value.terminated


def test_foreign_bus_connection_is_not_activated(recorder, monkeypatch):
    recorder.start()
    monkeypatch.setattr(recorder, '_owns', lambda _: False)
    recorder.run.reset_mock()
    assert not recorder.stop().success
    recorder.run.assert_not_called()
    assert recorder.popen.return_value.terminated


@pytest.mark.parametrize('duration', [0, 4, -1, 901, '60', True, None, float('inf')])
def test_duration_is_bounded_before_start(recorder, duration):
    assert recorder.start(duration=duration).error == 'INVALID_RECORDING'
    recorder.popen.assert_not_called()


def test_missing_backend_and_wrong_session_do_not_launch(recorder, monkeypatch):
    monkeypatch.setenv('XDG_SESSION_TYPE', 'x11')
    assert recorder.start().error == 'RECORDING_UNAVAILABLE'
    recorder.popen.assert_not_called()


def test_stop_timeout_kills_only_owned_process_and_reports_failure(recorder, monkeypatch):
    recorder.start()
    recorder.target.write_bytes(b'unfinished')
    original = recorder.process.wait
    monkeypatch.setattr(recorder.process, 'wait', Mock(side_effect=[subprocess.TimeoutExpired('spectacle', 20), 0]))
    assert not recorder.stop().success
    assert recorder.popen.return_value.terminated


def test_invalid_video_probe_is_rejected(recorder, monkeypatch):
    recorder.start()
    recorder.target.write_bytes(b'invalid')
    monkeypatch.setattr(recorder, '_valid_video', lambda: False)
    assert not recorder.stop().success


def test_automatic_deadline_stops_session(recorder, monkeypatch):
    recorder.start(duration=5)
    recorder.deadline = 0
    recorder.target.write_bytes(b'webm')
    runtime = Mock()
    monkeypatch.setattr('core.runtime.get_runtime', lambda: runtime)
    recorder._watch(recorder.done)
    assert recorder.process is None
    assert recorder.last.success
    runtime.enqueue.assert_called_once()


def test_dispatch_preserves_scope_and_artifact(monkeypatch):
    capture = Mock(return_value=SimpleNamespace(success=True, message='ok', error=None, artifact_path='/tmp/window.png'))
    monkeypatch.setattr(ScreenCapture, 'capture', capture)
    result = dispatch({'action': 'SCREENSHOT', 'scope': 'window'})
    capture.assert_called_once_with(scope='window')
    assert result.artifact_path == '/tmp/window.png'


def test_recording_uses_pc_policy_and_dispatch(recorder, monkeypatch):
    from core.action_executor import execute_action
    monkeypatch.setattr('core.capture.recording.screen_recorder', recorder)
    result = execute_action({'action': 'RECORDING_START', 'scope': 'region', 'duration': 15})
    assert result.success
    argv = recorder.popen.call_args.args[0]
    assert argv[argv.index('--record') + 1] == 'region'


def test_async_stop_keeps_status_available_until_slow_encoding_finishes(recorder, monkeypatch):
    recorder.start()
    recorder.target.write_bytes(b'video')
    entered, release = threading.Event(), threading.Event()
    waits = []
    original_wait = recorder.process.wait
    def slow_wait(timeout):
        waits.append(timeout)
        entered.set()
        assert release.wait(3), 'Le test doit débloquer la finalisation'
        return original_wait(timeout)
    monkeypatch.setattr(recorder.process, 'wait', slow_wait)
    monkeypatch.setattr(threading.Thread, 'start', recorder.real_thread_start)
    runtime = Mock()
    monkeypatch.setattr('core.runtime.get_runtime', lambda: runtime)
    try:
        result = recorder.stop_async()
        assert result.success and result.artifact_path is None
        assert entered.wait(2)
        assert 'sauvegarde' in recorder.status().message
        assert recorder.status().artifact_path is None
        assert recorder.start().error == 'FINALIZING'
        assert recorder.stop_async().artifact_path is None
        assert waits == [120]
    finally:
        release.set()
        if recorder.finalizer:
            recorder.finalizer.join(timeout=3)
    assert recorder.last.success and recorder.last.artifact_path
    assert not recorder.finalizing.is_set()
    assert not recorder.popen.return_value.terminated
    runtime.enqueue.assert_called_once()


def test_video_without_final_duration_is_not_claimed_complete(recorder):
    recorder.target = recorder.destination/'partial.webm'
    recorder.target.write_bytes(b'partial')
    recorder.run = Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps({
        'streams': [{'codec_type': 'video', 'width': 1366, 'height': 768}], 'format': {'size': '262144'}})))
    assert not recorder._valid_video()


def test_stop_action_uses_background_finalization(monkeypatch):
    from core.actions.models import ActionResult
    manager = Mock()
    manager.stop_async.return_value = ActionResult('RECORDING_STOP', True, 'Sauvegarde en cours.')
    monkeypatch.setattr('core.capture.recording.screen_recorder', manager)
    result = dispatch({'action': 'RECORDING_STOP'})
    assert result.success and result.artifact_path is None
    manager.stop_async.assert_called_once()
    manager.stop.assert_not_called()


def test_late_stop_from_old_session_cannot_stop_current_recording(recorder):
    old_session = recorder.done
    recorder.start()
    recorder.run.reset_mock()
    assert recorder.stop(expected_done=old_session) is None
    recorder.run.assert_not_called()
    assert recorder.process is not None
