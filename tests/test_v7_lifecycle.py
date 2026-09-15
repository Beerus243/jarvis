import socket
import struct
from unittest.mock import Mock
import pytest

from core.lifecycle import ApplicationLock
from core.proactivity.idle import IdleMonitor, packet, wire_string
from scripts.install_autostart import render, quoted


def test_single_instance_even_without_runtime():
    first, second = ApplicationLock(), ApplicationLock()
    try:
        assert first.acquire()
        assert not second.acquire()
        first.close()
        assert second.acquire()
    finally:
        first.close()
        second.close()


def test_background_mic_retry_has_no_greeting(monkeypatch):
    import main
    pipeline = Mock()
    pipeline.run_microphone.side_effect = [OSError('micro disconnected'), None]
    monkeypatch.setattr('voice.voice_pipeline.LocalWakeVoicePipeline.from_defaults', lambda **kw: pipeline)
    sleep = Mock()
    monkeypatch.setattr(main.time, 'sleep', sleep)
    assert main.main(['--background', '--no-proactive']) == 0
    pipeline.prepare_voice.assert_called_once_with(announce=False)
    assert pipeline.run_microphone.call_count == 2
    sleep.assert_called_once_with(5)


def test_foreground_mic_failure_is_reported(monkeypatch):
    import main
    pipeline = Mock()
    pipeline.run_microphone.side_effect = OSError('micro disconnected')
    monkeypatch.setattr('voice.voice_pipeline.LocalWakeVoicePipeline.from_defaults', lambda **kw: pipeline)
    assert main.main(['--no-proactive']) == 1


def test_silent_preparation_still_loads_configured_voice(monkeypatch):
    from voice.voice_pipeline import LocalWakeVoicePipeline
    speaker, prepare = Mock(), Mock()
    monkeypatch.setattr('voice.voice_manager.speak', speaker)
    monkeypatch.setattr('voice.voice_manager.prepare_voice', prepare)
    LocalWakeVoicePipeline(Mock(), Mock(), Mock(), speaker=speaker).prepare_voice(announce=False)
    prepare.assert_called_once()
    speaker.assert_not_called()


def test_service_starts_at_login_and_limits_restart(tmp_path):
    unit = render(tmp_path / 'Jarvis projet')
    assert 'WantedBy=graphical-session.target' in unit
    assert '--background' in unit
    assert 'Restart=on-failure' in unit
    assert 'StartLimitBurst=3' in unit
    assert 'TimeoutStopSec=150' in unit
    assert 'User=' not in unit
    assert quoted('/path/100%') == '"/path/100%%"'
    with pytest.raises(ValueError):
        quoted('/path\ninjection')


def test_idle_protocol_only_subscribes_to_activity(monkeypatch):
    monitor = IdleMonitor(clock=lambda: 42.)
    seat = packet(2, 0, struct.pack('=I', 11) + wire_string('wl_seat') + struct.pack('=I', 10))
    notifier = packet(2, 0, struct.pack('=I', 21) + wire_string('ext_idle_notifier_v1') + struct.pack('=I', 2))
    done = packet(3, 0, struct.pack('=I', 1))
    sock = Mock()
    # Fragment a frame, then actual input resumed, then EOF.
    stream = seat + notifier + done + packet(6, 1)
    sock.recv.side_effect = [stream[:11], stream[11:], b'']
    monkeypatch.setattr(socket, 'socket', lambda *a: sock)
    monkeypatch.setenv('XDG_RUNTIME_DIR', '/tmp')
    monitor._connect()
    assert monitor.ready
    assert monitor.idle_seconds() == 0
    requests = [call.args[0] for call in sock.sendall.call_args_list]
    assert requests[-1] == packet(5, 2, struct.pack('=III', 6, 0, 4))
    assert len(requests) == 5  # registry, sync, seat, notifier, idle; no keyboard/pointer


def test_idle_unknown_until_real_input():
    monitor = IdleMonitor()
    monitor.ready = True
    assert monitor.idle_seconds() is None


def test_install_preview_does_not_write_or_enable(monkeypatch, capsys):
    from scripts import install_autostart
    run = Mock(side_effect=AssertionError('preview must not mutate'))
    monkeypatch.setattr(install_autostart.subprocess, 'run', run)
    assert install_autostart.main([]) == 0
    assert '--background' in capsys.readouterr().out
    run.assert_not_called()


def test_background_sigterm_exits_cleanly_and_releases_lock(tmp_path):
    import os
    import subprocess
    import sys
    import select
    database = tmp_path / 'signal.sqlite3'
    script = '''
import signal
from types import SimpleNamespace
import main
from voice.voice_pipeline import LocalWakeVoicePipeline
def listen(**kwargs):
    print('TEST_READY', flush=True)
    signal.pause()
LocalWakeVoicePipeline.from_defaults = lambda **kwargs: SimpleNamespace(prepare_voice=lambda **kw: None, run_microphone=listen)
raise SystemExit(main.main(['--background', '--no-proactive']))
'''
    process = subprocess.Popen([sys.executable, '-u', '-c', script], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True,
                               env={**os.environ, 'JARVIS_STATE_DB': str(database)})
    try:
        # Read lines using readiness, not an unbounded wait for a child.
        import time
        deadline = time.monotonic() + 15
        ready = False
        received = b''
        while time.monotonic() < deadline and process.poll() is None:
            readable, _, _ = select.select([process.stdout], [], [], .5)
            if readable:
                received += os.read(process.stdout.fileno(), 65536)
                if b'TEST_READY' in received:
                    ready = True
                    break
        assert ready
        process.terminate()
        output, error = process.communicate(timeout=15)
        assert process.returncode == 0, error
        assert 'Arrêt demandé' in output
        import fcntl
        with open(str(database) + '.main.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_migration_accepts_known_launcher_but_preserves_custom_units(tmp_path):
    from scripts.install_autostart import legacy_unit
    old = '''[Unit]
Description=JARVIS Personal Assistant
After=graphical-session.target pipewire.service
Wants=pipewire.service
[Service]
Type=simple
WorkingDirectory=%h/dev/jarvis
ExecStart=%h/dev/jarvis/.venv-kokoro-cuda/bin/python %h/dev/jarvis/main.py --voice
Environment=PYTHONUNBUFFERED=1
Restart=on-failure
RestartSec=5
[Install]
WantedBy=default.target
'''
    assert legacy_unit(old, tmp_path)
    assert not legacy_unit(old.replace('Type=simple', 'Type=simple\nExecStartPre=/custom/script'), tmp_path)
    assert not legacy_unit(old.replace('PYTHONUNBUFFERED=1', 'CUSTOM=value'), tmp_path)
