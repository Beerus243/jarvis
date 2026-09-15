from threading import Event, Thread
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core.runtime import Runtime, add_reminder
from core.state_store import get_store
from core.vision.client import GroqVisionClient
from core.vision.capture import VisionError
from core.vision.watch import VisualWatch
from core.vision.watch_commands import handle_watch_command


@pytest.fixture
def watching():
    now = [0]
    capture = Mock(return_value=b'first-image')
    assess = Mock(return_value={'state': 'waiting', 'evidence': 'En cours'})
    enqueue, cancel = Mock(), Mock()
    watch = VisualWatch(enqueue, cancel, capture=capture, assess=assess, clock=lambda: now[0])
    watch.start('compilation')
    return watch, now, capture, assess, enqueue, cancel


def advance(watching, seconds=30):
    watching[1][0] += seconds
    watching[0].step()


def test_inactive_watch_never_captures():
    capture = Mock()
    watch = VisualWatch(Mock(), Mock(), capture=capture)
    watch.step()
    capture.assert_not_called()


def test_identical_images_skip_api_and_interval_is_respected(watching):
    watch, _, capture, assess, *_ = watching
    watch.step()
    watch.step()
    assert capture.call_count == 1
    advance(watching)
    assert capture.call_count == 2
    assert assess.call_count == 1
    assert watch.snapshot()['state'] == 'RUNNING'


@pytest.mark.parametrize('state', ['complete', 'error'])
def test_two_matching_observations_produce_one_alert_even_for_identical_image(state, watching):
    watch, _, capture, assess, enqueue, _ = watching
    assess.return_value = {'state': state, 'evidence': 'Un indice visible'}
    watch.step()
    enqueue.assert_not_called()
    advance(watching)
    advance(watching)
    assert watch.snapshot()['state'] == 'COMPLETED'
    assert capture.call_count == assess.call_count == 2
    enqueue.assert_called_once()
    assert enqueue.call_args.kwargs['visual_watch_id'] == watch.snapshot()['id']


def test_uncertainty_breaks_confirmation_streak(watching):
    watch, _, capture, assess, enqueue, _ = watching
    capture.side_effect = [b'a', b'b', b'c', b'd']
    assess.side_effect = [{'state': s, 'evidence': 'visible'} for s in ('complete', 'unknown', 'complete', 'complete')]
    watch.step()
    advance(watching)
    advance(watching)
    enqueue.assert_not_called()
    advance(watching)
    enqueue.assert_called_once()


def test_no_evidence_never_triggers_completion(watching):
    watch, _, _, assess, enqueue, _ = watching
    assess.return_value = {'state': 'complete', 'evidence': ''}
    watch.step()
    advance(watching)
    enqueue.assert_not_called()


def test_error_watch_ignores_completion(watching):
    watch, _, _, assess, enqueue, _ = watching
    watch.stop()
    watch.start('error')
    assess.return_value = {'state': 'complete', 'evidence': '100 %'}
    watch.step()
    advance(watching)
    enqueue.assert_not_called()


def test_busy_defers_capture_but_not_expiration(watching):
    watch, now, capture, _, enqueue, _ = watching
    watch.busy.set()
    watch.step()
    capture.assert_not_called()
    now[0] = 300
    watch.expire()
    assert watch.snapshot()['state'] == 'EXPIRED'
    enqueue.assert_called_once()


def test_analysis_budget_cannot_be_exceeded(watching):
    watch, _, capture, assess, enqueue, _ = watching
    watch.stop()
    watch.start('download', max_analyses=2)
    capture.side_effect = [b'a', b'b', b'c']
    watch.step()
    advance(watching)
    advance(watching)
    assert assess.call_count == 2
    assert watch.snapshot()['state'] == 'LIMIT'
    enqueue.assert_called_once()


def test_three_errors_stop_watch_without_leaking_error_data(watching):
    watch, _, capture, _, enqueue, _ = watching
    capture.side_effect = RuntimeError('private-image-or-key')
    watch.step()
    advance(watching)
    advance(watching)
    advance(watching)
    assert capture.call_count == 3
    assert watch.snapshot()['state'] == 'FAILED'
    assert 'private' not in enqueue.call_args.args[1]


def test_stop_during_capture_prevents_upload(watching):
    watch, _, capture, assess, enqueue, cancel = watching
    capture.side_effect = lambda: (watch.stop(), b'image')[1]
    watch.step()
    assess.assert_not_called()
    enqueue.assert_not_called()
    cancel.assert_called_once()
    assert watch.snapshot()['state'] == 'CANCELLED'


def test_stop_discards_inflight_result_and_allows_new_watch(watching):
    watch, _, _, assess, enqueue, _ = watching
    def late(*_):
        watch.stop()
        watch.start('download')
        return {'state': 'complete', 'evidence': 'ancien résultat'}
    assess.side_effect = late
    old_id = watch.snapshot()['id']
    watch.step()
    assert watch.snapshot()['id'] != old_id
    assert watch.snapshot()['analyses'] == 0
    enqueue.assert_not_called()


def test_deadline_is_checked_before_upload_and_after_result(watching):
    watch, now, capture, assess, enqueue, _ = watching
    def delayed_capture():
        now[0] = 301
        return b'image'
    capture.side_effect = delayed_capture
    watch.step()
    assess.assert_not_called()
    enqueue.assert_called_once()
    assert watch.snapshot()['state'] == 'EXPIRED'


def test_only_one_analysis_can_run_at_a_time(watching):
    watch, _, capture, _, _, _ = watching
    entered, release = Event(), Event()
    def blocked_capture():
        entered.set()
        assert release.wait(5)
        return b'image'
    capture.side_effect = blocked_capture
    worker = Thread(target=watch.step)
    worker.start()
    try:
        assert entered.wait(5)
        watch.step()
        assert capture.call_count == 1
        assert 'déjà active' in watch.start('download')
        watch.stop()
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive()


@pytest.mark.parametrize('options', [{'duration': 901}, {'duration': 0}, {'interval': 1},
    {'interval': float('inf')}, {'max_analyses': 11}, {'max_analyses': 0}])
def test_invalid_budgets_are_rejected(options):
    watch = VisualWatch(Mock(), Mock())
    with pytest.raises(ValueError):
        watch.start('compilation', **options)


def test_disabled_provider_stops_before_capture(watching):
    watch, _, capture, _, enqueue, _ = watching
    watch.enabled = lambda: False
    watch.step()
    capture.assert_not_called()
    assert watch.snapshot()['state'] == 'FAILED'
    enqueue.assert_called_once()


def test_expired_watch_can_be_replaced_without_waiting_for_worker(watching):
    watch, now, _, _, enqueue, cancel = watching
    old_id = watch.snapshot()['id']
    now[0] = 300
    assert 'activée' in watch.start('download')
    assert watch.snapshot()['goal'] == 'download'
    assert watch.snapshot()['id'] != old_id
    enqueue.assert_called_once()
    cancel.assert_called_once_with(old_id)


@pytest.fixture
def command_runtime(monkeypatch):
    runtime = SimpleNamespace(visual_watch=Mock())
    monkeypatch.setattr('core.runtime.get_runtime', lambda: runtime)
    monkeypatch.setattr('core.vision.client.GroqVisionClient', Mock())
    monkeypatch.setenv('JARVIS_VISION_PROVIDER', 'groq')
    return runtime


@pytest.mark.parametrize('command,goal,duration', [
    ('surveille cette compilation', 'compilation', 300),
    ('Surveille ma compilation pendant quinze minutes', 'compilation', 900),
    ('surveille cette compilation et préviens-moi quand elle termine pendant 2 minutes', 'compilation', 120),
    ('surveille ce téléchargement', 'download', 300),
    ('préviens-moi quand le téléchargement est terminé pendant une minute', 'download', 60),
    ('préviens-moi si une erreur apparaît à l’écran', 'error', 300),
])
def test_start_commands_reach_runtime(command, goal, duration, command_runtime):
    handle_watch_command(command)
    command_runtime.visual_watch.start.assert_called_once_with(goal, duration=duration)


@pytest.mark.parametrize('command', ['surveille cette compilation pendant 99 minutes',
    'surveille cette compilation pendant zéro minutes', 'surveille ma webcam',
    'préviens-moi quand le téléchargement est terminé pendant une heure'])
def test_unsupported_requests_never_start(command, command_runtime):
    assert isinstance(handle_watch_command(command), str)
    command_runtime.visual_watch.start.assert_not_called()


def test_control_commands_and_unrelated_commands(command_runtime):
    handle_watch_command('arrête la surveillance')
    handle_watch_command('que surveilles-tu')
    command_runtime.visual_watch.stop.assert_called_once()
    command_runtime.visual_watch.status.assert_called_once()
    assert handle_watch_command('ne surveille pas mon écran') is None
    assert handle_watch_command('quelle heure est-il') is None


def test_no_runtime_does_not_promise_monitoring(monkeypatch):
    monkeypatch.setattr('core.runtime.get_runtime', lambda: None)
    assert '--no-proactive' in handle_watch_command('surveille cette compilation')


@pytest.mark.parametrize('raw', ['not json', '[]', '{"state":"complete"}',
    '{"state":"maybe","evidence":"texte"}', '{"state":"complete","evidence":5}',
    '{"state":[],"evidence":"texte"}'])
def test_malformed_model_decisions_are_rejected(raw):
    client = GroqVisionClient(client=Mock())
    client.analyze_image = Mock(return_value=raw)
    with pytest.raises(VisionError):
        client.assess_image(b'jpeg', 'compilation')


def test_structured_observation_requires_visible_evidence():
    client = GroqVisionClient(client=Mock())
    client.analyze_image = Mock(return_value='{"state":"complete","evidence":""}')
    assert client.assess_image(b'jpeg', 'compilation')['state'] == 'unknown'
    assert client.analyze_image.call_args.kwargs['response_format'] == {'type': 'json_object'}


def test_watch_alert_respects_busy_silent_and_cancellation():
    runtime = Runtime(pc_provider=lambda: {}, personal_provider=lambda: {})
    watch = runtime.visual_watch
    now = [0]
    watch.clock = lambda: now[0]
    watch.capture = Mock(return_value=b'image')
    watch.assess = Mock(return_value={'state': 'complete', 'evidence': 'BUILD SUCCESS'})
    watch.start('compilation')
    watch.step()
    now[0] = 30
    watch.step()
    sink = Mock(return_value=True)
    runtime.busy.set()
    runtime.deliver(sink)
    sink.assert_not_called()
    runtime.busy.clear()
    get_store().put('settings', 'silent', True)
    runtime.deliver(sink)
    sink.assert_not_called()
    get_store().put('settings', 'silent', False)
    runtime.deliver(sink)
    runtime.deliver(sink)
    sink.assert_called_once()
    runtime.enqueue('pending-watch', 'à annuler', visual_watch_id=watch.snapshot()['id'])
    watch.stop()
    runtime.deliver(sink)
    sink.assert_called_once()


def test_slow_vision_does_not_block_reminders(monkeypatch):
    import time
    entered, release, delivered = Event(), Event(), Event()
    runtime = Runtime(notify=lambda _: delivered.set(), pc_provider=lambda: {}, personal_provider=lambda: {},
                      interval=.02, presence_provider=lambda: {'state': 'active'})
    def capture():
        entered.set()
        assert release.wait(5)
        return b'image'
    runtime.visual_watch.capture = capture
    runtime.visual_watch.assess = Mock(return_value={'state': 'waiting', 'evidence': ''})
    runtime.visual_watch.start('compilation')
    runtime.start()
    try:
        assert entered.wait(5)
        add_reminder('pause', time.time() + .1)
        assert delivered.wait(5)
        assert not release.is_set()
    finally:
        runtime.visual_watch.stop()
        release.set()
        runtime.stop()


def test_restart_cancels_stale_visual_alerts_but_not_reminders():
    store = get_store()
    runtime = Runtime(interval=100)
    runtime.enqueue('old-watch', 'ancienne observation', visual_watch_id='old')
    runtime.enqueue('reminder', 'rappel', reminder_id='r1')
    runtime.start()
    try:
        assert runtime.visual_watch.snapshot() is None
        assert store.get('notifications', 'old-watch')['status'] == 'CANCELLED'
        assert store.get('notifications', 'reminder')['status'] == 'PENDING'
    finally:
        runtime.stop()


def test_forget_also_stops_active_surveillance(monkeypatch):
    from core.vision.commands import handle_vision_command
    runtime = Runtime(interval=100)
    monkeypatch.setattr('core.runtime.get_runtime', lambda: runtime)
    runtime.visual_watch.start('compilation')
    result = handle_vision_command('oublie ce que tu as vu')
    assert 'effacé' in result and 'arrêtée' in result
    assert runtime.visual_watch.snapshot()['state'] == 'CANCELLED'


from tests.test_main_commands import routed


def test_default_main_voice_can_start_query_and_stop_watch(monkeypatch, routed):
    import main
    from voice.voice_pipeline import LocalWakeVoicePipeline
    from voice.wake_word_engine import WakeDetection
    runtime = Runtime(interval=100)
    # Les actions vocales sont réelles ; les périphériques et l'IA sont doublés.
    runtime._watch_loop = lambda: runtime.stopping.wait()
    runtime.visual_watch.capture = Mock(return_value=b'image')
    runtime.visual_watch.assess = Mock(return_value={'state': 'waiting', 'evidence': ''})
    monkeypatch.setattr('core.runtime.Runtime', lambda **_: runtime)
    monkeypatch.setattr('core.vision.client.GroqVisionClient', Mock())
    monkeypatch.setenv('JARVIS_VISION_PROVIDER', 'groq')
    detector = Mock()
    detector.detect.return_value = WakeDetection(True, .9, 'hey_jarvis', 1.)
    commands = iter(['surveille cette compilation pendant deux minutes', 'que surveilles-tu', 'arrête la surveillance'])
    speaker = Mock(return_value=True)
    pipeline = LocalWakeVoicePipeline(detector, lambda _: next(commands), main.think,
                                      speaker=speaker, feedback=lambda: None)
    def microphone(**_):
        responses = []
        for _ in range(3):
            pipeline.feed_wake_chunk(b'wake')
            responses.append(pipeline.process_command_audio(b'command')['response'])
        assert 'activée' in responses[0]
        assert 'active' in responses[1]
        assert 'arrêtée' in responses[2]
        assert runtime.visual_watch.snapshot()['state'] == 'CANCELLED'
    monkeypatch.setattr(pipeline, 'run_microphone', microphone)
    monkeypatch.setattr(LocalWakeVoicePipeline, 'from_defaults', lambda **_: pipeline)
    assert main.main([]) == 0
    runtime.visual_watch.capture.assert_not_called()
    routed[0].assert_not_called()
    routed[1].assert_not_called()
