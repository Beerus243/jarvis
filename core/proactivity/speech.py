"""Contrôle de la prise de parole spontanée, indépendant du focus et du sommeil."""
from core.command_understanding import normalize_command
from core.state_store import get_store

KEY = 'proactive_speech'
ENABLED = 'enabled'
MUTED = 'muted'

ENABLE_PHRASES = {
    'active le mode proactif',
    'tu peux reparler',
    'reprends tes interventions',
    'sors du mode muet',
}
MUTE_PHRASES = {
    'passe en mode muet',
    'mets toi en mode silencieux',
    'arrete de me parler spontanement',
    'ne prends plus l initiative de me parler',
}
STATUS_PHRASES = {
    'quel est ton mode actuel',
    'est ce que tu es en mode muet',
}


def _strip_jarvis(text):
    return text[7:].lstrip() if text.startswith('jarvis ') else text


def mode():
    value = get_store().get('settings', KEY, ENABLED)
    return MUTED if value == MUTED else ENABLED


def is_muted():
    return mode() == MUTED


def set_mode(value):
    if value not in {ENABLED, MUTED}:
        raise ValueError('Mode de parole spontanée inconnu.')
    get_store().put('settings', KEY, value)
    return value


def status_line():
    return 'Mode muet.' if is_muted() else 'Mode proactif.'


def speech_blocked(runtime=None, store=None):
    """True si aucune annonce spontanée ne doit être prononcée."""
    store = store or get_store()
    if runtime is not None and runtime.busy.is_set():
        return True
    if store.get('settings', 'silent', False):
        return True
    return is_muted()


def handle_speech_command(message):
    text = _strip_jarvis(normalize_command(message))
    if text in MUTE_PHRASES:
        set_mode(MUTED)
        return 'Mode muet. Je n’interviens plus spontanément.'
    if text in ENABLE_PHRASES:
        set_mode(ENABLED)
        return 'Mode proactif. Je pourrai te parler si le contexte le justifie.'
    if text in STATUS_PHRASES:
        if is_muted():
            return 'Mode muet. Je n’interviens pas spontanément ; dis « Jarvis » pour une commande.'
        return 'Mode proactif. Je peux prendre la parole si le contexte le justifie.'
    return None
