"""Thread-safe, bounded UI observations; observers cannot interrupt the Core."""
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import logging
import threading
import uuid

_lock = threading.RLock()
_listeners = set()
_history = deque(maxlen=1000)
_state = {'type': 'state.changed', 'state': 'idle', 'detail': 'JARVIS prêt'}
_voice = None
_sequence = 0
_sequence_initialized = False
_request_context = ContextVar('jarvis_ui_request', default=None)

ORIGINS = {'ui_text', 'ui_voice', 'wake_word', 'proactive', 'system'}


@contextmanager
def request_scope(request_id=None, origin='system', conversation_id=None):
    current = _request_context.get() or {}
    context = {
        'requestId': request_id or current.get('requestId') or uuid.uuid4().hex,
        'origin': origin if origin in ORIGINS else current.get('origin', 'system'),
        'conversationId': conversation_id or current.get('conversationId'),
    }
    token = _request_context.set(context)
    try:
        yield context
    finally:
        _request_context.reset(token)


def request_context():
    return dict(_request_context.get() or {})


def now():
    return datetime.now(timezone.utc).isoformat()


def publish(event):
    global _sequence, _sequence_initialized, _state
    with _lock:
        if not _sequence_initialized:
            try:
                from core.conversation import max_operation_sequence
                _sequence = max(_sequence, max_operation_sequence())
            except Exception:
                logging.getLogger(__name__).exception('UI event sequence restore failed')
            _sequence_initialized = True
        _sequence += 1
        context = _request_context.get() or {}
        event = {
            **event,
            'eventId': event.get('eventId') or uuid.uuid4().hex,
            'sequence': _sequence,
            'historical': False,
            'timestamp': event.get('timestamp') or now(),
        }
        for key in ('requestId', 'origin', 'conversationId'):
            if event.get(key) is None and context.get(key) is not None:
                event[key] = context[key]
        if event['type'] == 'state.changed':
            _state = event
        if event['type'] not in {'transcription.updated'} or event.get('text'):
            _history.append(event)
        listeners = tuple(_listeners)
    if event.get('requestId') and event['type'] in {
        'command.updated', 'tool.updated', 'state.changed', 'voice.state',
        'activity.created', 'confirmation.required', 'confirmation.resolved',
        'message.updated', 'transcription.updated', 'notification.created',
    } and (event['type'] != 'transcription.updated' or event.get('phase') == 'final'):
        try:
            from core.conversation import record_operation_event
            record_operation_event(event)
        except Exception:
            logging.getLogger(__name__).exception('UI operation event persistence failed')
    for listener in listeners:
        try:
            listener(event)
        except Exception:
            logging.getLogger(__name__).exception('UI observer failed')


def state(value, detail=''):
    publish({'type': 'state.changed', 'state': value, 'detail': detail})


def voice_state(value, detail=''):
    publish({'type': 'voice.state', 'state': value, 'detail': detail})


def message(role, text):
    publish({'type': 'message.updated', 'message': {
        'id': uuid.uuid4().hex, 'role': role, 'text': str(text),
        'timestamp': now(), 'status': 'sent', 'tools': [],
    }, **request_context()})


def activity(text, *, kind='system', status='info'):
    publish({'type': 'activity.created', 'activity': {
        'id': uuid.uuid4().hex, 'timestamp': now(), 'type': kind,
        'message': text, 'status': status,
    }, **request_context()})


def command(request_id, origin, text, status, *, conversation_id=None, detail=None,
            tool=None, result=None, duration_ms=None):
    with request_scope(request_id, origin, conversation_id):
        payload = {
            'requestId': request_id,
            'origin': origin,
            'text': str(text),
            'status': status,
            'updatedAt': now(),
        }
        if conversation_id:
            payload['conversationId'] = conversation_id
        if detail:
            payload['detail'] = str(detail)
        if tool:
            payload['tool'] = str(tool)
        if result is not None:
            payload['result'] = str(result)[:2000]
        if duration_ms is not None:
            payload['durationMs'] = max(0, int(duration_ms))
        publish({'type': 'command.updated', 'command': payload})


def tool(name, status, *, result=None, error=None, duration_ms=None):
    context = request_context()
    if not context.get('requestId'):
        return
    payload = {
        'requestId': context['requestId'],
        'name': str(name),
        'status': status,
        'timestamp': now(),
    }
    if result is not None:
        payload['result'] = str(result)[:2000]
    if error is not None:
        payload['error'] = str(error)[:2000]
    if duration_ms is not None:
        payload['durationMs'] = max(0, int(duration_ms))
    command(context['requestId'], context.get('origin', 'system'), name,
            'tool_started' if status == 'started' else 'tool_completed' if status == 'completed' else 'failed',
            conversation_id=context.get('conversationId'), tool=name,
            result=result if result is not None else error, duration_ms=duration_ms)
    publish({'type': 'tool.updated', 'tool': payload})


def subscribe(listener):
    with _lock:
        _listeners.add(listener)
    def unsubscribe():
        with _lock:
            _listeners.discard(listener)
    return unsubscribe


def snapshot():
    with _lock:
        history = [{**event, 'historical': True} for event in _history]
        if not history or history[-1].get('sequence') != _state.get('sequence'):
            history.append({**_state, 'historical': True})
        return history


def sequence():
    with _lock:
        return _sequence


def initialize_sequence():
    global _sequence, _sequence_initialized
    with _lock:
        if not _sequence_initialized:
            from core.conversation import max_operation_sequence
            _sequence = max(_sequence, max_operation_sequence())
            _sequence_initialized = True
        return _sequence


def set_voice(pipeline):
    global _voice
    with _lock:
        _voice = pipeline
    publish({'type': 'session.capabilities', 'voice': pipeline is not None})


def get_voice():
    with _lock:
        return _voice
