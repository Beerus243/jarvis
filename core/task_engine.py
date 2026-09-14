"""Tâches durables, bornées, confirmables et annulables entre les étapes."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
import threading
import uuid

from core.action_planner import plan_actions
from core.intent import detect_work_environment_intent
from core.action_executor import execute_action
from core.state_store import get_store

PLANNED, RUNNING, WAITING_CONFIRMATION, COMPLETED, FAILED, CANCELLED, PAUSED = (
    'PLANNED', 'RUNNING', 'WAITING_CONFIRMATION', 'COMPLETED', 'FAILED', 'CANCELLED', 'PAUSED')


@dataclass
class Task:
    goal: str
    steps: list = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: str = PLANNED
    created_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())
    current_step: int = 0
    results: list = field(default_factory=list)
    in_flight: bool = False
    error: str | None = None
    agent: bool = False


_active_task = None
_execution_lock = threading.Lock()


def _action(item):
    if isinstance(item, dict):
        return dict(item)
    if hasattr(item, 'action'):
        action = item.action
        if action == 'OPEN_VSCODE' and item.message.startswith(('~', '/')):
            return {'action': action, 'target': item.message}
        return dict(action) if isinstance(action, dict) else {'action': action}
    return {'action': item}


def _save(task, *, allow_resume=False):
    def persist(value):
        result = asdict(task)
        if value and (value['status'] == CANCELLED or (value['status'] == PAUSED and not allow_resume)):
            result['status'] = value['status']
        return result
    saved = get_store().mutate('tasks', task.id, persist)
    task.status = saved['status']
    return task


def load_task(task_id):
    value = get_store().get('tasks', task_id)
    return Task(**value) if value else None


def list_tasks():
    return [Task(**value) for _, value in get_store().items('tasks')]


def create_task(goal, steps=None, *, agent=False):
    global _active_task
    if steps is None and detect_work_environment_intent(goal):
        routine = get_store().get('settings', 'work_routine')
        steps = routine or [{'action': 'OPEN_BROWSER'}, {'action': 'OPEN_VSCODE', 'target': '~/dev/jarvis'},
                           {'action': 'OPEN_APPLICATION', 'target': 'spotify'}]
    elif steps is None:
        from core.action_parser import parse_actions
        steps = parse_actions(goal)
    steps = [_action(step) for step in steps]
    if len(steps) > 12:
        raise ValueError('Une tâche est limitée à 12 étapes.')
    task = Task(goal, steps, agent=agent)
    _active_task = task
    get_store().put('session', 'active_task', task.id)
    return _save(task)


def get_active_task():
    task_id = get_store().get('session', 'active_task')
    task = load_task(task_id) if task_id else None
    return task if task and task.status not in {COMPLETED, CANCELLED} else None


def cancel_task(task_id=None):
    task = load_task(task_id) if task_id else get_active_task()
    if not task or task.status in {CANCELLED, COMPLETED}:
        return False
    def cancel(value):
        if value:
            value['status'] = CANCELLED
        return value
    get_store().mutate('tasks', task.id, cancel)
    from core.pending_action import get_pending, clear_pending
    pending = get_pending()
    if pending and pending.get('task_id') == task.id:
        clear_pending()
    return True


def pause_task(task_id=None):
    task = load_task(task_id) if task_id else get_active_task()
    if not task or task.status in {COMPLETED, CANCELLED}:
        return False
    get_store().mutate('tasks', task.id, lambda value: {**value, 'status': PAUSED})
    return True


def execute_task(task=None, confirmation=False, dispatcher=None):
    """Une étape terminée est persistée avant de considérer l'étape suivante.

    Une étape dont le résultat est inconnu après un crash n'est jamais rejouée
    automatiquement. La confirmation porte uniquement sur l'étape courante.
    """
    task = task or get_active_task()
    if task is None:
        return None
    with _execution_lock:
        task = load_task(task.id) or task
        if task.status in {COMPLETED, CANCELLED}:
            return task, []
        if task.in_flight:
            task.status = PAUSED
            task.error = 'Résultat de la dernière étape inconnu après interruption. Vérifiez-le avant de recréer une tâche.'
            _save(task)
            return task, []
        task.status = RUNNING
        task.error = None
        _save(task, allow_resume=True)
        results = []
        while task.current_step < len(task.steps) or task.agent:
            latest = load_task(task.id)
            if latest.status in {CANCELLED, PAUSED}:
                task.status = latest.status
                return task, results
            if task.current_step == len(task.steps) and task.agent:
                if task.current_step >= 8:
                    task.status, task.error = PAUSED, 'Limite de 8 étapes atteinte ; bilan requis.'
                    _save(task)
                    break
                from core.tool_agent import next_action
                try:
                    action = next_action(task.goal, task.results)
                except Exception as error:
                    task.status, task.error = FAILED, f'Planification indisponible : {error}'
                    _save(task)
                    break
                if action is None:
                    task.status = COMPLETED if task.results else FAILED
                    task.error = 'Aucune action réalisable proposée.' if not task.results else 'Mission arrêtée par le planificateur ; consulte les résultats des étapes.'
                    _save(task)
                    break
                if action in task.steps:
                    task.status, task.error = PAUSED, 'Action répétée refusée ; bilan requis.'
                    _save(task)
                    break
                task.steps.append(action)
            task.in_flight = True
            def claim(value):
                if value and value['status'] in {CANCELLED, PAUSED}:
                    return value
                return asdict(task)
            claimed = get_store().mutate('tasks', task.id, claim)
            if claimed['status'] in {CANCELLED, PAUSED}:
                return Task(**claimed), results
            action = task.steps[task.current_step]
            result = execute_action(action, confirmation=confirmation, dispatcher=dispatcher)
            confirmation = False
            results.append(result)
            task.in_flight = False
            if not result.success:
                task.status = WAITING_CONFIRMATION if result.policy == 'CONFIRMATION_REQUIRED' else FAILED
                task.error = result.message
                if task.status == WAITING_CONFIRMATION:
                    from core.pending_action import set_pending
                    pending = set_pending(action, task_id=task.id)
                    task.error = f"Confirmer {pending['id']} : {action} ?"
            else:
                task.results.append(asdict(result))
                task.current_step += 1
                task.status = COMPLETED if task.current_step == len(task.steps) and not task.agent else RUNNING
            def progress(value):
                updated = asdict(task)
                if value and value['status'] in {CANCELLED, PAUSED}:
                    updated['status'] = value['status']
                return updated
            saved = get_store().mutate('tasks', task.id, progress)
            task = Task(**saved)
            if task.status != RUNNING:
                break
        if not task.steps and task.status == RUNNING:
            task.status, task.error = FAILED, 'Aucune étape exécutable.'
            _save(task)
        return task, results


def task_dict(task):
    return asdict(task) if task else None
