"""Préférences sourcées et hypothèses ; aucune conversion implicite en certitude."""
from datetime import datetime
import statistics
import time
from core.state_store import get_store


def event(kind, details, *, now=None):
    entry = {'kind': kind, 'at': time.time() if now is None else now, 'details': details}
    get_store().mutate('v7', 'events', lambda items: ((items or []) + [entry])[-500:])


def preference(key, default=None):
    item = get_store().get('v7_preferences', key)
    return item['value'] if item and item.get('state') == 'confirmed' else default


def confirm(key, value, *, now=None, source='déclaration de Fabrice'):
    now = time.time() if now is None else now
    if key == 'break_minutes' and (type(value) is not int or not 5 <= value <= 240):
        raise ValueError('Choisis une pause après 5 à 240 minutes de travail actif.')
    item = {'value': value, 'state': 'confirmed', 'source': source, 'at': now}
    get_store().put('v7_preferences', key, item)
    if key == 'break_minutes':
        get_store().delete('v7', 'break_hypothesis')
        get_store().delete('v7', 'break_learning_blocked')
    event('preference_confirmed', {'key': key, 'value': value}, now=now)
    return item


def forget_break():
    store = get_store()
    store.delete('v7_preferences', 'break_minutes')
    store.delete('v7', 'break_hypothesis')
    store.delete('v7', 'break_samples')
    store.put('v7', 'break_learning_blocked', True)
    # L'oubli retire aussi les indices correspondants du petit journal local.
    store.mutate('v7', 'events', lambda items: [e for e in (items or []) if
        e['kind'] not in {'break_observed', 'break_hypothesis'} and e.get('details', {}).get('key') != 'break_minutes'])


def observe_break(session_id, seconds, *, now=None):
    now = time.time() if now is None else now
    if get_store().get('v7', 'break_learning_blocked', False) or not 300 <= seconds <= 14400:
        return
    item = {'session_id': session_id, 'minutes': round(seconds / 60),
            'day': datetime.fromtimestamp(now).astimezone().date().isoformat(), 'at': now,
            'source': 'pause explicitement déclarée ou confirmée'}
    samples = get_store().mutate('v7', 'break_samples', lambda values:
        ([s for s in (values or []) if s['session_id'] != session_id] + [item])[-30:])
    event('break_observed', item, now=now)
    recent = [s for s in samples if 0 <= now - s['at'] <= 30 * 86400]
    if len({s['day'] for s in recent}) < 3 or preference('break_minutes') is not None:
        return
    median = int(statistics.median(s['minutes'] for s in recent))
    if max(abs(s['minutes'] - median) for s in recent) > max(5, median * .25):
        return
    candidate = {'value': median, 'state': 'hypothesis', 'source': 'pauses sur au moins trois jours',
                 'observations': len(recent), 'at': now}
    get_store().put('v7', 'break_hypothesis', candidate)


def hypothesis(now=None):
    now = time.time() if now is None else now
    item = get_store().get('v7', 'break_hypothesis')
    if item and 0 <= now-item['at'] <= 30 * 86400:
        return item
    if item:
        get_store().delete('v7', 'break_hypothesis')
    return None


def describe():
    item = get_store().get('v7_preferences', 'break_minutes')
    candidate = hypothesis()
    if item:
        return f"Préférence confirmée : pause après {item['value']} minutes actives. Source : {item['source']}."
    if candidate:
        return f"Hypothèse à confirmer : pause vers {candidate['value']} minutes, d’après {candidate['observations']} pauses observées."
    return 'Je ne connais pas encore ton rythme de pause. Je ne déduis pas une habitude d’une simple mention.'
