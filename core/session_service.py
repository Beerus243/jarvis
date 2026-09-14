"""Dialogue déterministe : confirmations, rappels, tâches, attention et mémoire."""
from datetime import datetime, timedelta
import re
import time

from core.command_understanding import normalize_command
from core.state_store import get_store

CONFIRM = {'oui', 'confirme', 'je confirme', 'vas y', 'execute', 'ok', 'd accord'}
CANCEL = {'non', 'annule', 'annuler', 'stop', 'arrete', 'laisse tomber', 'pas maintenant'}
NUMBERS = {'un': 1, 'une': 1, 'deux': 2, 'trois': 3, 'cinq': 5, 'dix': 10, 'quinze': 15, 'trente': 30}


def _reminder(message):
    from core.runtime import add_reminder
    raw = message.strip()
    match = re.fullmatch(r'rappelle[- ]moi\s+dans\s+(\d+|un|une|deux|trois|cinq|dix|quinze|trente)\s+(secondes?|minutes?|heures?|jours?)\s+(?:de\s+|que\s+)?(.+)', raw, re.I)
    if match:
        amount = int(match[1]) if match[1].isdigit() else NUMBERS[match[1].lower()]
        multiplier = {'seconde': 1, 'minute': 60, 'heure': 3600, 'jour': 86400}[match[2].lower().rstrip('s')]
        item = add_reminder(match[3], time.time() + amount * multiplier)
        return f"Rappel {item['id']} enregistré pour {datetime.fromtimestamp(item['due_at']).astimezone():%d/%m à %H:%M:%S}."
    match = re.fullmatch(r'rappelle[- ]moi\s+(demain|aujourd.hui)\s+[aà]\s+(\d{1,2})[h:]?(\d{2})?\s+(?:de\s+|que\s+)?(.+)', raw, re.I)
    if match:
        when = datetime.now().astimezone().replace(hour=int(match[2]), minute=int(match[3] or 0), second=0, microsecond=0)
        if match[1].lower() == 'demain':
            when += timedelta(days=1)
        item = add_reminder(match[4], when.timestamp())
        return f"Rappel {item['id']} enregistré pour {when:%d/%m à %H:%M}."
    if normalize_command(raw).startswith('rappelle moi '):
        return 'Précise le délai : « rappelle-moi dans 10 minutes de faire une pause » ou « rappelle-moi demain à 9h de reprendre mon projet ».'
    return None


def handle_message(message, dispatcher=None):
    text = normalize_command(message)
    store = get_store()
    from core.pending_action import get_pending, consume, clear_pending
    from core.environment.pending_plan import get_pending as environment_pending
    pending = get_pending()
    if text in {'montre le plan', 'montre moi ce que tu ferais', 'simulation du plan'}:
        from core.environment.conversation_plan import format_plan
        plan = environment_pending()
        if plan:
            return format_plan(plan)
        if pending:
            return f"Action {pending['id']} en attente : {pending['action']}. Aucune exécution effectuée."
        return 'Aucun plan en attente.'
    explicit_confirm = pending and text == 'confirme ' + pending['id']
    explicit_cancel = pending and text == 'annule ' + pending['id']
    if pending and (text in CONFIRM | CANCEL or explicit_confirm or explicit_cancel):
        if environment_pending() and not (explicit_confirm or explicit_cancel):
            return f"Deux confirmations sont en attente. Pour l'action PC, dis « confirme {pending['id']} » ou « annule {pending['id']} »."
        if text in CANCEL or explicit_cancel:
            clear_pending()
            if pending.get('task_id'):
                from core.task_engine import cancel_task
                cancel_task(pending['task_id'])
            return 'Action annulée.'
        pending = consume()
        if not pending:
            return 'Cette confirmation a expiré ou a déjà été utilisée.'
        if pending.get('task_id'):
            from core.task_engine import load_task, execute_task
            task = load_task(pending['task_id'])
            if not task or task.status != 'WAITING_CONFIRMATION' or task.steps[task.current_step] != pending['action']:
                return 'La tâche a changé ; confirmation invalidée.'
            from core.runtime import get_runtime
            runtime = get_runtime()
            if runtime:
                runtime.submit(task.id, confirmation=True)
                return f"Reprise de la tâche {task.id[:8]}."
            task, _ = execute_task(task, confirmation=True, dispatcher=dispatcher)
            return f"Tâche {task.status}. {task.error or ''}".strip()
        from core.action_executor import execute_action
        result = execute_action(pending['action'], confirmation=True, dispatcher=dispatcher)
        return result

    if text in {'mode silencieux', 'ne me derange pas', 'desactive les notifications'}:
        store.put('settings', 'silent', True)
        return 'Mode silencieux activé. Les rappels restent enregistrés.'
    if text in {'desactive le mode silencieux', 'reprends les notifications', 'active les notifications'}:
        store.put('settings', 'silent', False)
        return 'Notifications réactivées.'
    if text.startswith('configure ma routine de travail '):
        from core.action_parser import parse_actions
        from core.action_policy import classify_action, BLOCKED_ACTION
        raw = re.sub(r'^configure ma routine de travail\s*:?\s*', '', message, flags=re.I)
        parts = re.split(r'\s+puis\s+', raw, flags=re.I)
        actions = [parse_actions(part) for part in parts]
        if not 1 <= len(actions) <= 12 or any(len(items) != 1 or items[0].get('needs_clarification') or
                classify_action(items[0]['action']) == BLOCKED_ACTION for items in actions):
            return 'Précise de 1 à 12 commandes connues séparées par « puis ».'
        store.put('settings', 'work_routine', [items[0] for items in actions])
        return f'Routine enregistrée : {len(actions)} étapes. Dis « au boulot » pour la lancer.'
    if text == 'montre ma routine de travail':
        return str(store.get('settings', 'work_routine') or 'Routine par défaut : navigateur, VS Code dans ~/dev/jarvis, Spotify.')
    if text in {'rappelle moi plus tard', 'plus tard', 'rappelle moi dans dix minutes'}:
        notice = store.get('session', 'last_notification')
        if not notice:
            return 'Aucune notification à reporter.'
        from core.runtime import add_reminder
        add_reminder(notice['message'].removeprefix('Rappel : '), time.time() + 600)
        return 'Je te le rappellerai dans 10 minutes.'
    if text in {'liste mes rappels', 'mes rappels'}:
        items = [v for _, v in store.items('reminders') if v['status'] == 'SCHEDULED']
        return '\n'.join(f"{v['id']} : {v['message']} — {datetime.fromtimestamp(v['due_at']):%d/%m %H:%M}" for v in items) or 'Aucun rappel prévu.'
    match = re.fullmatch(r'annule le rappel ([a-f0-9]{8})', text)
    if match:
        item = store.get('reminders', match[1])
        if not item:
            return 'Rappel introuvable.'
        item['status'] = 'CANCELLED'
        store.put('reminders', match[1], item)
        for key, notice in store.items('notifications'):
            if notice.get('reminder_id') == match[1]:
                notice['status'] = 'CANCELLED'
                store.put('notifications', key, notice)
        return 'Rappel annulé.'
    try:
        reminder = _reminder(message)
    except ValueError:
        return 'Cette date ou cette durée est invalide.'
    if reminder:
        return reminder

    from core.task_engine import get_active_task, list_tasks, cancel_task, pause_task, execute_task
    # L'identifiant permet de retrouver une ancienne tâche après une autre mission.
    match = re.fullmatch(r'(reprends|annule|pause) la tache ([a-f0-9]{8,32})', text)
    if match:
        matches = [task for task in list_tasks() if task.id.startswith(match[2])]
        if len(matches) != 1:
            return 'Identifiant de tâche introuvable ou ambigu.'
        store.put('session', 'active_task', matches[0].id)
        text = {'reprends': 'reprends la tache', 'annule': 'annule la tache', 'pause': 'pause la tache'}[match[1]]
    if text.startswith('mission '):
        from core.task_engine import create_task
        from core.runtime import get_runtime
        goal = message.split(maxsplit=1)[1]
        task = create_task(goal, steps=[], agent=True)
        if get_runtime():
            get_runtime().submit(task.id)
            return f'Mission {task.id[:8]} démarrée, limitée à 8 étapes. Dis « annule la tâche » pour arrêter.'
        task, _ = execute_task(task, dispatcher=dispatcher)
        return f'Mission {task.status}. {task.error or ""}'
    if text in {'mes taches', 'liste mes taches', 'ou en es tu'}:
        tasks = sorted(list_tasks(), key=lambda t: t.created_at, reverse=True)[:10]
        return '\n'.join(f'{t.id[:8]} : {t.goal} — {t.status} ({t.current_step}/{len(t.steps)})' for t in tasks) or 'Aucune tâche enregistrée.'
    if text in {'annule la tache', 'annule ma tache'}:
        return 'Tâche annulée. L’étape déjà en cours peut se terminer.' if cancel_task() else 'Aucune tâche active.'
    if text in {'mets la tache en pause', 'pause la tache'}:
        return 'La tâche sera suspendue après l’étape en cours.' if pause_task() else 'Aucune tâche active.'
    if text in {'reprends la tache', 'continue la tache'}:
        task = get_active_task()
        if not task:
            return 'Aucune tâche à reprendre.'
        if task.status in {'RUNNING', 'WAITING_CONFIRMATION'}:
            if task.status == 'WAITING_CONFIRMATION' and not get_pending():
                pause_task(task.id)
                return 'La confirmation a expiré. Dis « reprends la tâche » pour revoir l’action exacte.'
            return 'La tâche est en cours ou attend sa confirmation.'
        from core.runtime import get_runtime
        if get_runtime():
            get_runtime().submit(task.id)
            return f'Reprise de la tâche {task.id[:8]}.'
        task, _ = execute_task(task, dispatcher=dispatcher)
        return f'Tâche {task.status}. {task.error or ""}'.strip()
    if text in CANCEL and not environment_pending() and get_active_task():
        cancel_task()
        return 'Tâche annulée après l’étape en cours.'

    from memory.service import handle_memory_command
    return handle_memory_command(message)
