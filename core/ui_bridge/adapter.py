"""Translate the desktop protocol to existing Core services and policies."""
import json
import shutil
from pathlib import Path
from . import events

STATUS = {'PLANNED': 'scheduled', 'RUNNING': 'running', 'WAITING_CONFIRMATION': 'waiting',
          'COMPLETED': 'completed', 'FAILED': 'failed', 'CANCELLED': 'cancelled', 'PAUSED': 'paused'}


def task_payload(task):
    total = len(task.steps)
    steps = []
    for index, step in enumerate(task.steps):
        status = 'completed' if index < task.current_step else 'pending'
        if index == task.current_step:
            if task.status == 'FAILED':
                status = 'failed'
            elif task.in_flight:
                status = 'running'
        steps.append({'title': str(step.get('action', step)) +
                      (f" · {step['target']}" if step.get('target') else ''), 'status': status})
    return {'id': task.id, 'title': task.goal, 'status': STATUS.get(task.status, 'paused'),
            'progress': 100 if task.status == 'COMPLETED' else min(100, round(100 * task.current_step / total)) if total else 0,
            'agent': 'Agent JARVIS' if task.agent else 'JARVIS Core',
            'startedAt': task.created_at if task.status != 'PLANNED' else None, 'steps': steps}


def confirmations():
    from core.pending_action import get_pending
    from core.environment.pending_plan import get_pending as environment_pending
    result = []
    pending = get_pending()
    if pending:
        action = pending['action']
        item = {'id': pending['id'], 'title': 'Confirmer cette action',
                'description': json.dumps(action, ensure_ascii=False),
                'target': str(action.get('target') or action.get('action') or 'JARVIS')}
        if pending.get('task_id'):
            item['taskId'] = pending['task_id']
        result.append(item)
    plan = environment_pending()
    if plan:
        from core.environment.conversation_plan import format_plan
        result.append({'id': plan.plan_id, 'title': "Confirmer le plan d’environnement",
                       'description': format_plan(plan),
                       'target': str(getattr(plan.intent, 'environment', 'Environnement'))})
    return result


def snapshot():
    from core.task_engine import list_tasks
    from core.runtime import get_runtime
    tasks = sorted(list_tasks(), key=lambda task: task.created_at)[-100:]
    runtime = get_runtime()
    running = [task for task in tasks if task.status == 'RUNNING']
    agent = {'id': 'jarvis-core', 'name': 'JARVIS Core',
             'description': 'Moteur Python local et tâches persistantes',
             'status': 'running' if running else 'idle',
             'task': running[-1].goal if running else None,
             'lastEvent': 'Runtime actif' if runtime else 'Session interactive',
             'actions': sum(len(task.results) for task in tasks)}
    return {'tasks': [task_payload(task) for task in tasks], 'agents': [agent],
            'confirmations': confirmations()}


def system_snapshot():
    from core.hardware_monitor import cpu_stats, memory_stats
    from core.pc_context import get_pc_context
    from main import VERSION
    cpu, memory = cpu_stats(), memory_stats()
    context = get_pc_context()
    try:
        disk = shutil.disk_usage(Path.home())
        storage = round(100 * disk.used / disk.total, 1)
    except OSError:
        storage = None
    active = context.get('active_window') or {}
    return {'cpu': round(cpu.usage_percent, 1) if cpu.usage_percent is not None else None,
            'ram': round(memory.usage_percent, 1) if memory.usage_percent is not None else None,
            'storage': storage,
            'ramTotal': round(memory.total_bytes / 1024 ** 3, 1) if memory.total_bytes else None,
            'network': context.get('network', {}).get('available'),
            'microphone': events.get_voice() is not None,
            'audio': context.get('audio', {}).get('server'),
            'window': str(active.get('title') or active.get('application') or 'Indisponible'),
            'version': f'{VERSION} · Python Core', 'latency': None,
            'applications': [{'id': str(app.get('id') or app['name']).lower(), 'name': app['name'],
                              'detail': 'Processus actif' if app.get('running') else 'Fermé',
                              'status': 'active' if app.get('running') else 'closed'}
                             for app in context.get('applications', [])]}


def respond(identifier, approved):
    # The shared command lock prevents voice/terminal/UI from replacing a plan.
    from core.command_session import command_lock
    from core.pending_action import get_pending
    from core.environment.pending_plan import get_pending as environment_pending
    with command_lock:
        pending = get_pending()
        plan = environment_pending()
        if pending and pending['id'] == identifier:
            from core.session_service import handle_message
            response = handle_message(('confirme ' if approved else 'annule ') + identifier)
        elif plan and plan.plan_id == identifier:
            from dataclasses import replace
            from core.environment.command_handler import handle_environment_intent
            response = handle_environment_intent(
                replace(plan.intent, intent='ENVIRONMENT_CONFIRM' if approved else 'ENVIRONMENT_CANCEL', capability=None),
                expected_plan_id=identifier)
        else:
            raise ValueError('Cette confirmation a expiré, a changé ou a déjà été utilisée.')
        events.message('jarvis', getattr(response, 'message', response))
        return response


def dispatch(command):
    kind = command['type']
    if kind == 'command.send':
        from core.command_session import process_command
        from core.runtime import get_runtime
        runtime = get_runtime()
        was_busy = runtime.busy.is_set() if runtime else False
        if runtime:
            runtime.busy.set()
        try:
            with events.request_scope(
                command.get('requestId'), command.get('origin', 'ui_text'),
                command.get('conversationId'),
            ):
                return process_command(command['text'])
        finally:
            if runtime and not was_busy:
                runtime.busy.clear()
    if kind == 'confirmation.respond':
        return respond(command['id'], command['approved'])
    if kind == 'task.cancel':
        from core.task_engine import cancel_task, load_task
        task = load_task(command['id'])
        if not task or task.status in {'CANCELLED', 'COMPLETED', 'FAILED'} or not cancel_task(task.id):
            raise ValueError('Tâche introuvable ou déjà terminée.')
        events.activity('Tâche annulée. Une étape déjà en cours peut se terminer.', kind='task', status='warning')
        return
    if kind in {'voice.start', 'voice.stop'}:
        pipeline = events.get_voice()
        if pipeline is None:
            raise ValueError('Le microphone Python est indisponible ou démarre encore.')
        if kind == 'voice.start':
            pipeline.request_ui_listen(
                command['requestId'], command.get('origin', 'ui_voice'),
                command.get('conversationId', 'default'),
            )
        else:
            pipeline.request_ui_stop()
        return
    if kind == 'voice.speak':
        pipeline = events.get_voice()
        if pipeline is None:
            raise ValueError('Kokoro est indisponible tant que le microphone Python démarre.')
        pipeline.request_ui_speech(
            command['text'], command['requestId'], command.get('conversationId', 'default'),
        )
        return
    raise ValueError('Type de commande inconnu.')
