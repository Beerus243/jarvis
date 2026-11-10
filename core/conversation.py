import json
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import re
import uuid
from config.settings import CONVERSATION_FILE
from core.json_store import atomic_write
from core.json_store import update

history = []
_active_conversation = ContextVar('jarvis_conversation', default=None)
_active_history = ContextVar('jarvis_conversation_history', default=None)
_CONVERSATION_DIR = CONVERSATION_FILE.parent / 'conversations'


def _conversation_path(conversation_id):
    if conversation_id == 'default':
        return CONVERSATION_FILE
    if not isinstance(conversation_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', conversation_id):
        raise ValueError('Identifiant de conversation invalide.')
    return _CONVERSATION_DIR / f'{conversation_id}.json'


def _active_path():
    conversation_id = _active_conversation.get()
    return _conversation_path(conversation_id) if conversation_id else CONVERSATION_FILE


def operation_history_path(conversation_id):
    conversation_path = _conversation_path(conversation_id)
    if conversation_id == 'default':
        return CONVERSATION_FILE.with_name('conversation.events.json')
    return conversation_path.with_suffix('.events.json')


def record_operation_event(event):
    conversation_id = event.get('conversationId') or 'default'
    path = operation_history_path(conversation_id)
    def append(items):
        if any(item.get('eventId') == event.get('eventId') for item in items):
            return items
        return sorted([*items, event], key=lambda item: item.get('sequence', 0))[-2000:]
    update(path, append, default=[])


def load_operation_events(conversation_id):
    path = operation_history_path(conversation_id)
    try:
        events = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return []
    return [*events]


def max_operation_sequence():
    paths = [CONVERSATION_FILE.with_name('conversation.events.json'),
             *_CONVERSATION_DIR.glob('*.events.json')]
    maximum = 0
    for path in paths:
        try:
            for event in json.loads(path.read_text(encoding='utf-8')):
                maximum = max(maximum, int(event.get('sequence', 0)))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return maximum


@contextmanager
def conversation_scope(conversation_id):
    path = _conversation_path(conversation_id)
    try:
        messages = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        if conversation_id != 'default':
            raise ValueError('Conversation introuvable.')
        messages = []
    conversation_token = _active_conversation.set(conversation_id)
    history_token = _active_history.set(messages)
    try:
        yield conversation_id
    finally:
        _active_history.reset(history_token)
        _active_conversation.reset(conversation_token)


def create_conversation(conversation_id):
    path = _conversation_path(conversation_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError('Cette conversation existe déjà.')
    atomic_write(path, [])
    return conversation_id


def list_conversations():
    items = []
    paths = [CONVERSATION_FILE, *_CONVERSATION_DIR.glob('*.json')]
    if not CONVERSATION_FILE.exists():
        items.append({'id': 'default', 'title': 'Conversation existante',
                      'updatedAt': datetime.fromtimestamp(0, timezone.utc).isoformat(),
                      'messageCount': 0})
    for path in paths:
        if not path.is_file():
            continue
        conversation_id = 'default' if path == CONVERSATION_FILE else path.stem
        try:
            messages = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            continue
        first_user = next((item.get('message', '') for item in messages if item.get('role') == 'user'), '')
        items.append({
            'id': conversation_id,
            'title': (first_user[:72] or 'Nouvelle conversation'),
            'updatedAt': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            'messageCount': len(messages),
        })
    return sorted(items, key=lambda item: item['updatedAt'], reverse=True)

def _write_conversation(conversation):
    atomic_write(CONVERSATION_FILE, conversation)


def get_history():
    scoped = _active_history.get()
    return scoped if scoped is not None else history


def get_last_user_message():

    for message in reversed(get_history()):

        if message["role"] == "user":
            return message["message"]

    return None


def get_recent_history(limit=5):
    messages = get_history()
    if messages:
        return messages[-limit:]
    return load_conversation()[-limit:]


def clear_history():
    scoped = _active_history.get()
    if scoped is not None:
        scoped.clear()
    else:
        history.clear()



# ============================================================
# CHARGER LA CONVERSATION
# ============================================================

def load_conversation():

    try:

        with open(_active_path(), "r", encoding='utf-8') as f:
            return json.load(f)

    except FileNotFoundError:

        return []


# ============================================================
# AJOUTER UN MESSAGE
# ============================================================

def add_message(role, message):
    record = {"role": role, "message": message, "id": uuid.uuid4().hex,
              "timestamp": datetime.now(timezone.utc).isoformat()}
    try:
        from core.ui_bridge.events import request_context
        record.update({key: value for key, value in request_context().items() if value is not None})
    except ImportError:
        pass
    scoped = _active_history.get()
    if scoped is not None:
        scoped.append(record)
        del scoped[:-100]
    else:
        history.append(record)
        del history[:-100]

    path = _active_path()
    def append(conversation):
        return (conversation + [record])[-100:]
    update(path, append, default=[])
    if scoped is not None:
        scoped[:] = load_conversation()


def get_last_message():
    recent = get_recent_history(1)
    return recent[-1] if recent else None


# ============================================================
# RÉCUPÉRER LE CONTEXTE
# ============================================================

def get_context():

    conversation = load_conversation()

    return conversation


# ============================================================
# EFFACER LE CONTEXTE
# ============================================================

def clear_conversation():
    scoped = _active_history.get()
    if scoped is not None:
        scoped.clear()
    else:
        history.clear()
    atomic_write(_active_path(), [])
