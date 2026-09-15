"""Régressions de concurrence et d'indisponibilité avant les sessions longues."""
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core.runtime import Runtime
from core.state_store import get_store
from core.vision.capture import VisionError
from core.vision.providers import LocalVisionClient
from core.vision.routines import VisualRoutines
from core.vision.watch import VisualWatch


def slow_rule(monkeypatch):
    entered, release = threading.Event(), threading.Event()
    def pc():
        entered.set()
        assert release.wait(5)
        return {'active_window': {'available': True, 'application': 'code'}}
    watch = VisualWatch(Mock(), Mock())
    rule = VisualRoutines(watch, pc_provider=pc)
    monkeypatch.setattr('core.vision.routines.get_client', lambda: Mock())
    rule.start()
    worker = threading.Thread(target=rule.step)
    worker.start()
    assert entered.wait(2)
    return rule, watch, release, worker


def test_routine_stop_does_not_wait_for_slow_context_or_restart(monkeypatch):
    rule, watch, release, worker = slow_rule(monkeypatch)
    stopped = threading.Event()
    stopper = threading.Thread(target=lambda: (rule.stop(), stopped.set()))
    try:
        stopper.start()
        assert stopped.wait(.5), 'Un capteur lent ne doit pas bloquer l’arrêt.'
    finally:
        release.set()
        worker.join(2)
        stopper.join(2)
    assert watch.snapshot() is None


def test_silence_during_context_read_defers_routine_start(monkeypatch):
    rule, watch, release, worker = slow_rule(monkeypatch)
    try:
        get_store().put('settings', 'silent', True)
    finally:
        release.set()
        worker.join(2)
    assert watch.snapshot() is None
    assert 'attente' in rule.status()


@pytest.mark.parametrize('application', ['barcode-scanner', 'video-decoder', 'decode-player'])
def test_coding_routine_does_not_match_substrings_in_other_app_names(application, monkeypatch):
    watch = VisualWatch(Mock(), Mock())
    rule = VisualRoutines(watch, pc_provider=lambda: {'active_window': {'available': True, 'application': application}})
    monkeypatch.setattr('core.vision.routines.get_client', lambda: Mock())
    rule.start()
    rule.step()
    assert watch.snapshot() is None


def test_failing_routine_does_not_cancel_independent_watch():
    runtime = Runtime()
    runtime.visual_watch.start('compilation')
    runtime.visual_routines.step = Mock(side_effect=RuntimeError('sensor unavailable'))
    runtime.visual_watch.step = Mock()
    runtime.stopping = Mock()
    runtime.stopping.wait.side_effect = [False, True]
    runtime._watch_loop()
    assert runtime.visual_watch.snapshot()['state'] == 'RUNNING'
    runtime.visual_watch.step.assert_called_once()


@pytest.mark.parametrize('message', [None, [], 'broken'])
def test_malformed_local_reply_is_an_operational_error(message, monkeypatch):
    monkeypatch.setattr(LocalVisionClient, '_post', lambda *a, **kw: {'capabilities': ['vision']})
    client = LocalVisionClient('installed-vision')
    monkeypatch.setattr(client, '_post', lambda *a, **kw: {'message': message})
    with pytest.raises(VisionError):
        client.analyze_image(b'\xff\xd8\xfftest', 'lis', 'screen')


@pytest.mark.parametrize('application', ['code', 'Code', 'org.kde.konsole', 'org.kde.kate', 'codium'])
def test_exact_development_apps_still_start_routine(application, monkeypatch):
    watch = VisualWatch(Mock(), Mock())
    rule = VisualRoutines(watch, pc_provider=lambda: {'active_window': {'available': True, 'application': application}})
    monkeypatch.setattr('core.vision.routines.get_client', lambda: Mock())
    rule.start()
    rule.step()
    assert watch.snapshot()['state'] == 'RUNNING'


@pytest.mark.parametrize('capabilities', [None, 'vision', {}, 1])
def test_malformed_local_capabilities_are_not_accepted(capabilities, monkeypatch):
    monkeypatch.setattr(LocalVisionClient, '_post', lambda *a, **kw: {'capabilities': capabilities})
    with pytest.raises(VisionError):
        LocalVisionClient('installed-vision')


def test_old_context_cannot_start_a_newly_armed_routine(monkeypatch):
    rule, watch, release, worker = slow_rule(monkeypatch)
    try:
        rule.stop()
        rule.start()
    finally:
        release.set()
        worker.join(2)
    assert watch.snapshot() is None
    assert 'attente' in rule.status()


def test_busy_command_during_context_read_defers_start(monkeypatch):
    rule, watch, release, worker = slow_rule(monkeypatch)
    try:
        watch.busy.set()
    finally:
        release.set()
        worker.join(2)
    assert watch.snapshot() is None


def test_pc_cache_lifetime_starts_after_slow_collection(monkeypatch):
    from core import pc_context
    clock = [0.0]
    def slow_kwin():
        clock[0] += 5
        return {'active_window': {}, 'windows': []}
    kwin = Mock(side_effect=slow_kwin)
    monkeypatch.setattr(pc_context.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(pc_context.time, 'time', lambda: 1000 + clock[0])
    monkeypatch.setattr(pc_context, 'get_kwin_context', kwin)
    for name in ('_battery', '_network', '_audio', '_cpu_gpu_memory', 'get_known_applications'):
        monkeypatch.setattr(pc_context, name, lambda: {})
    pc_context.clear_pc_context_cache()
    try:
        first = pc_context.get_pc_context()
        assert first['observed_at'] == 1000
        assert pc_context.get_pc_context() is first
        assert kwin.call_count == 1
        clock[0] += 2.1
        assert pc_context.get_pc_context() is not first
        assert kwin.call_count == 2
    finally:
        pc_context.clear_pc_context_cache()


def test_pc_cache_expiry_ignores_wall_clock_rollback(monkeypatch):
    from core import pc_context
    monotonic, wall = [10.0], [1000.0]
    monkeypatch.setattr(pc_context.time, 'monotonic', lambda: monotonic[0])
    monkeypatch.setattr(pc_context.time, 'time', lambda: wall[0])
    monkeypatch.setattr(pc_context, 'get_kwin_context', lambda: {'active_window': {}, 'windows': []})
    for name in ('_battery', '_network', '_audio', '_cpu_gpu_memory', 'get_known_applications'):
        monkeypatch.setattr(pc_context, name, lambda: {})
    pc_context.clear_pc_context_cache()
    try:
        first = pc_context.get_pc_context()
        monotonic[0] += 3
        wall[0] -= 3600
        assert pc_context.get_pc_context() is not first
    finally:
        pc_context.clear_pc_context_cache()
