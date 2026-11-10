"""Real service adapters with isolated state; no OS action, STT or LLM request."""
import asyncio
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest
from core.ui_bridge import adapter, events
from core.ui_bridge.server import UIBridge, validate


@pytest.mark.parametrize('payload', [[], {}, {'type': 'command.send', 'text': ''},
    {'type': 'command.send', 'text': 'a' * 2001},
    {'type': 'confirmation.respond', 'id': 'abc', 'approved': 'false'},
    {'type': 'task.cancel', 'id': ''}, {'type': 'session.subscribe', 'protocolVersion': True}])
def test_protocol_rejects_invalid_commands(payload):
    with pytest.raises(ValueError):
        validate(json.dumps(payload))


def test_command_reaches_shared_brain_and_publishes_reply(monkeypatch):
    calls, observed = [], []
    def think(text):
        calls.append(text)
        return 'Réponse réelle du cerveau de test'
    monkeypatch.setattr('core.brain.think', think)
    unsubscribe = events.subscribe(observed.append)
    try:
        adapter.dispatch({'type': 'command.send', 'requestId': 'request-test',
                  'origin': 'ui_text', 'conversationId': 'conversation-test',
                  'text': 'liste mes tâches'})
    finally:
        unsubscribe()
    assert calls == ['liste mes tâches']
    messages = [item['message'] for item in observed if item['type'] == 'message.updated']
    assert [(item['role'], item['text']) for item in messages] == [
        ('user', 'liste mes tâches'), ('jarvis', 'Réponse réelle du cerveau de test')]
    assert all(item['requestId'] == 'request-test' for item in observed)
    assert all(item['origin'] == 'ui_text' for item in observed)
    assert all(item['conversationId'] == 'conversation-test' for item in observed)


def test_conversation_scopes_isolate_and_preserve_legacy_json(monkeypatch, tmp_path):
    from core import conversation
    legacy = tmp_path / 'conversation.json'
    legacy.write_text(json.dumps([{'role': 'user', 'message': 'legacy'}]), encoding='utf-8')
    monkeypatch.setattr(conversation, 'CONVERSATION_FILE', legacy)
    monkeypatch.setattr(conversation, '_CONVERSATION_DIR', tmp_path / 'conversations')
    conversation.create_conversation('thread-a')
    conversation.create_conversation('thread-b')
    with conversation.conversation_scope('thread-a'):
        conversation.add_message('user', 'A only')
        assert conversation.get_recent_history()[-1]['message'] == 'A only'
    with conversation.conversation_scope('thread-b'):
        assert conversation.get_history() == []
        conversation.add_message('user', 'B only')
    with conversation.conversation_scope('thread-a'):
        assert [item['message'] for item in conversation.get_history()] == ['A only']
    assert json.loads(legacy.read_text(encoding='utf-8')) == [{'role': 'user', 'message': 'legacy'}]
    assert {item['id'] for item in conversation.list_conversations()} == {'default', 'thread-a', 'thread-b'}


def test_operation_events_persist_per_conversation(monkeypatch, tmp_path):
    from core import conversation
    legacy = tmp_path / 'conversation.json'
    legacy.write_text('[]', encoding='utf-8')
    monkeypatch.setattr(conversation, 'CONVERSATION_FILE', legacy)
    monkeypatch.setattr(conversation, '_CONVERSATION_DIR', tmp_path / 'conversations')
    conversation.create_conversation('thread-a')
    with events.request_scope('request-a', 'ui_text', 'thread-a'):
        events.command('request-a', 'ui_text', 'Question', 'started', conversation_id='thread-a')
        events.tool('GET_TIME', 'started')
    history = conversation.load_operation_events('thread-a')
    assert [event['type'] for event in history] == ['command.updated', 'command.updated', 'tool.updated']
    assert all(event['requestId'] == 'request-a' for event in history)
    assert all(event['conversationId'] == 'thread-a' for event in history)
    assert conversation.load_operation_events('default') == []


def test_wrong_expired_and_replayed_confirmation_never_executes(monkeypatch):
    from core.pending_action import set_pending, get_pending
    calls = []
    monkeypatch.setattr('core.action_executor.execute_action', lambda action, **kwargs: calls.append(action) or 'OK')
    pending = set_pending({'action': 'CLOSE_APPLICATION', 'target': 'test'})
    with pytest.raises(ValueError):
        adapter.respond('wrong-id', True)
    assert get_pending()['id'] == pending['id'] and calls == []
    adapter.respond(pending['id'], True)
    assert len(calls) == 1
    with pytest.raises(ValueError):
        adapter.respond(pending['id'], True)
    expired = set_pending({'action': 'CLOSE_APPLICATION', 'target': 'test'}, now=0)
    with pytest.raises(ValueError):
        adapter.respond(expired['id'], True)
    assert len(calls) == 1


def test_atomic_confirmation_claim_keeps_replacement():
    from core.pending_action import set_pending, get_pending, consume
    old = set_pending({'action': 'OLD'})
    new = set_pending({'action': 'NEW'})
    assert consume(expected_id=old['id']) is None
    assert get_pending()['id'] == new['id']


def test_decline_and_cancel_change_actual_core_state(monkeypatch):
    from core.pending_action import set_pending, get_pending
    from core.task_engine import create_task, load_task
    monkeypatch.setattr('core.action_executor.execute_action', lambda *a, **k: pytest.fail('Must not execute'))
    task = create_task('test UI', steps=[{'action': 'OPEN_BROWSER'}])
    pending = set_pending(task.steps[0], task_id=task.id)
    adapter.respond(pending['id'], False)
    assert get_pending() is None
    assert load_task(task.id).status == 'CANCELLED'
    second = create_task('cancel UI', steps=[{'action': 'OPEN_BROWSER'}])
    adapter.dispatch({'type': 'task.cancel', 'id': second.id})
    assert load_task(second.id).status == 'CANCELLED'
    with pytest.raises(ValueError):
        adapter.dispatch({'type': 'task.cancel', 'id': 'does-not-exist'})


def test_environment_confirmation_stale_id_and_expiry():
    from core.environment.intent import detect_environment_intent
    from core.environment.pending_plan import set_pending, get_pending
    plan = set_pending(detect_environment_intent('prépare mon environnement Android'))
    with pytest.raises(ValueError):
        adapter.respond('ENV-old', True)
    assert get_pending() is plan
    adapter.respond(plan.plan_id, False)
    assert get_pending() is None
    plan = set_pending(detect_environment_intent('prépare mon environnement Android'))
    plan.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
    with pytest.raises(ValueError):
        adapter.respond(plan.plan_id, True)


def test_missing_telemetry_is_unknown_not_fake(monkeypatch):
    monkeypatch.setattr('core.hardware_monitor.cpu_stats', lambda: SimpleNamespace(usage_percent=None))
    monkeypatch.setattr('core.hardware_monitor.memory_stats', lambda: SimpleNamespace(usage_percent=None, total_bytes=None))
    monkeypatch.setattr('core.pc_context.get_pc_context', lambda: {})
    system = adapter.system_snapshot()
    assert system['cpu'] is None and system['ram'] is None and system['ramTotal'] is None
    assert system['network'] is None and system['audio'] is None and system['latency'] is None
    assert system['version'].endswith('Python Core')


def test_voice_stop_after_transcription_prevents_brain():
    from voice.voice_pipeline import LocalWakeVoicePipeline
    from voice.wake_word_engine import VoiceState
    pipeline = LocalWakeVoicePipeline(SimpleNamespace(), lambda _: 'ouvre une application',
                                     lambda _: pytest.fail('Cancelled audio reached brain'))
    pipeline.state = VoiceState.COMMAND_LISTENING
    pipeline.request_ui_stop()
    assert pipeline.process_command_audio(b'audio')['cancelled']


def test_ui_can_queue_a_kokoro_replay_without_direct_audio_access():
    queued = []
    events.set_voice(SimpleNamespace(request_ui_speech=lambda text, request_id, conversation_id: queued.append((text, request_id, conversation_id))))
    try:
        adapter.dispatch({'type': 'voice.speak', 'requestId': 'voice-replay-1',
                          'conversationId': 'conversation-test', 'text': 'Réponse à jouer'})
    finally:
        events.set_voice(None)
    assert queued == [('Réponse à jouer', 'voice-replay-1', 'conversation-test')]


def test_socket_origin_path_subscription_and_real_dispatch(monkeypatch):
    from websockets.asyncio.client import connect
    from websockets.exceptions import InvalidStatus
    calls = []
    monkeypatch.setattr(adapter, 'snapshot', lambda: {'tasks': [], 'agents': [], 'confirmations': []})
    monkeypatch.setattr(adapter, 'system_snapshot', lambda: None)
    def dispatch(command):
        calls.append(command)
        events.message('jarvis', 'socket-test-reply')
    monkeypatch.setattr(adapter, 'dispatch', dispatch)
    bridge = UIBridge(port=0).start()
    async def scenario():
        url = f'ws://127.0.0.1:{bridge.port}'
        for path, origin in [('/ws', 'https://untrusted.example'), ('/wrong', 'http://localhost:3000')]:
            with pytest.raises(InvalidStatus):
                async with connect(url + path, origin=origin, proxy=None):
                    pytest.fail('Untrusted handshake accepted')
        async with connect(url + '/ws', origin='http://localhost:3000', proxy=None) as socket:
            await socket.send(json.dumps({'type': 'command.send', 'text': 'too early'}))
            notice = json.loads(await asyncio.wait_for(socket.recv(), 3))
            assert notice['type'] == 'notification.created' and not calls
            await socket.send(json.dumps({'type': 'session.subscribe', 'protocolVersion': 1}))
            first = json.loads(await asyncio.wait_for(socket.recv(), 3))
            assert first['type'] == 'session.reset'
            request = {'type': 'command.send', 'requestId': 'socket-request-1',
                       'origin': 'ui_text', 'conversationId': 'default', 'text': 'hello'}
            await socket.send(json.dumps(request))
            for _ in range(250):
                event = json.loads(await asyncio.wait_for(socket.recv(), 3))
                if event['type'] == 'message.updated' and event['message']['text'] == 'socket-test-reply':
                    break
            else:
                pytest.fail('No real reply')
            assert len(calls) == 1
            assert calls == [request]
            await socket.send(json.dumps(request))
            for _ in range(250):
                event = json.loads(await asyncio.wait_for(socket.recv(), 3))
                if (event.get('type') == 'command.updated'
                        and event.get('requestId') == 'socket-request-1'
                        and 'aucune nouvelle exécution' in event['command'].get('detail', '')):
                    break
            else:
                pytest.fail('No duplicate-request acknowledgment')
            assert calls == [request]
    try:
        asyncio.run(scenario())
    finally:
        bridge.stop()
    assert not bridge.thread.is_alive()


def test_control_command_request_id_is_idempotent(monkeypatch):
    from websockets.asyncio.client import connect
    calls = []
    monkeypatch.setattr(adapter, 'dispatch', lambda command: calls.append(command))
    monkeypatch.setattr(adapter, 'snapshot', lambda: {'tasks': [], 'agents': [], 'confirmations': []})
    monkeypatch.setattr(adapter, 'system_snapshot', lambda: None)
    bridge = UIBridge(port=0).start()
    async def scenario():
        async with connect(f'ws://127.0.0.1:{bridge.port}/ws', proxy=None) as socket:
            await socket.send(json.dumps({'type': 'session.subscribe', 'protocolVersion': 2,
                                          'conversationId': 'default'}))
            while json.loads(await asyncio.wait_for(socket.recv(), 3))['type'] != 'session.synced':
                pass
            command = {'type': 'voice.speak', 'requestId': 'replay-once',
                       'origin': 'ui_voice', 'conversationId': 'default', 'text': 'Test'}
            await socket.send(json.dumps(command))
            await socket.send(json.dumps(command))
            while True:
                event = json.loads(await asyncio.wait_for(socket.recv(), 3))
                if (event.get('type') == 'command.updated'
                        and event.get('requestId') == 'replay-once'
                        and 'aucune nouvelle exécution' in event['command'].get('detail', '')):
                    break
            assert calls == [command]
    try:
        asyncio.run(scenario())
    finally:
        bridge.stop()


@pytest.mark.parametrize('cancel', [False, True])
def test_ui_uses_existing_mic_and_stop_discards_audio(monkeypatch, cancel):
    import sys
    from voice.voice_pipeline import LocalWakeVoicePipeline
    calls, streams, observed = [], [], []
    class Stream:
        closed = False
        def read(self, count, **kwargs):
            return b'\0\0' * count
        def stop_stream(self):
            pass
        def close(self):
            self.closed = True
    def open_stream(**kwargs):
        stream = Stream()
        streams.append(stream)
        return stream
    pa = SimpleNamespace(open=open_stream, terminate=lambda: None)
    monkeypatch.setitem(sys.modules, 'pyaudio', SimpleNamespace(PyAudio=lambda: pa, paInt16=8))
    monkeypatch.setitem(sys.modules, 'speech_recognition', SimpleNamespace(AudioData=lambda *args: args))
    pipeline = LocalWakeVoicePipeline(SimpleNamespace(reset=lambda: None),
        lambda audio: 'liste mes tâches', lambda text: calls.append(text) or 'OK', feedback=lambda: None)
    opened = []
    def on_event(event):
        if event['type'] == 'session.capabilities' and event['voice']:
            opened.append(True)
            if len(opened) == 1:
                pipeline.request_ui_listen('voice-request-1', 'ui_voice', 'voice-conversation')
            elif cancel:
                pipeline.request_ui_stop()
        observed.append(event)
    unsubscribe = events.subscribe(on_event)
    try:
        pipeline.run_microphone(max_cycles=1, command_seconds=.01)
    finally:
        unsubscribe()
    assert calls == ([] if cancel else ['liste mes tâches'])
    assert len(streams) == 2 and all(stream.closed for stream in streams)
    assert events.get_voice() is None
    transcription = [event for event in observed if event.get('type') == 'transcription.updated' and event.get('phase') == 'final']
    command = [event for event in observed if event.get('type') == 'command.updated' and event['command'].get('status') == 'received']
    if cancel:
        assert transcription == [] and command == []
    else:
        assert len(transcription) == len(command) == 1
        assert transcription[0]['requestId'] == command[0]['requestId'] == 'voice-request-1'
        assert transcription[0]['origin'] == command[0]['origin'] == 'ui_voice'
        assert transcription[0]['conversationId'] == command[0]['conversationId'] == 'voice-conversation'
