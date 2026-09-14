"""Une confirmation autorise une action précise, une seule fois, pendant 10 min."""
import time
import uuid
from core.state_store import get_store


def set_pending(action, *, task_id=None, now=None):
    current = time.time() if now is None else now
    pending = {'id': uuid.uuid4().hex[:8], 'action': action, 'task_id': task_id,
               'created_at': current, 'expires_at': current + 600}
    previous = []
    def replace(value):
        if value:
            previous.append(value)
        return pending
    get_store().mutate('session', 'pending_action', replace)
    if previous and previous[0].get('task_id') and previous[0]['task_id'] != task_id:
        def pause(value):
            if value and value['status'] == 'WAITING_CONFIRMATION':
                value.update(status='PAUSED', error='Confirmation remplacée. Reprends cette tâche pour revoir son action.')
            return value
        get_store().mutate('tasks', previous[0]['task_id'], pause)
    return pending


def get_pending(now=None):
    current = time.time() if now is None else now
    return get_store().mutate('session', 'pending_action',
        lambda value: value if value and value['expires_at'] > current else None)


def consume(now=None):
    current = time.time() if now is None else now
    claimed = []
    def take(value):
        if value and value['expires_at'] > current:
            claimed.append(value)
        return None
    get_store().mutate('session', 'pending_action', take)
    return claimed[0] if claimed else None


def clear_pending():
    get_store().delete('session', 'pending_action')
