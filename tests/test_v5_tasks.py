from unittest.mock import Mock

from core.task_engine import create_task, execute_task, load_task, pause_task, cancel_task
from core.pending_action import get_pending
from core.session_service import handle_message


def test_pause_persists_checkpoint_and_resume_skips_completed_steps(monkeypatch, tmp_path):
    monkeypatch.setattr('core.action_executor.MEMORY_FILE', tmp_path/'user.json')
    task = create_task('test', [{'action':'GET_TIME'}, {'action':'OPEN_BROWSER'}])
    seen = []
    def dispatch(action):
        seen.append(action['action'])
        if len(seen) == 1:
            pause_task(task.id)
        return True, 'ok'
    finished, _ = execute_task(task, dispatcher=dispatch)
    assert finished.status == 'PAUSED' and finished.current_step == 1
    # Recharger depuis le disque simule une nouvelle session.
    finished, _ = execute_task(load_task(task.id), dispatcher=dispatch)
    assert finished.status == 'COMPLETED'
    assert seen == ['GET_TIME', 'OPEN_BROWSER']


def test_cancel_between_steps_prevents_next_action(monkeypatch, tmp_path):
    monkeypatch.setattr('core.action_executor.MEMORY_FILE', tmp_path/'user.json')
    task = create_task('test', [{'action':'GET_TIME'}, {'action':'OPEN_BROWSER'}])
    def dispatch(_):
        cancel_task(task.id)
        return True, 'ok'
    dispatcher = Mock(side_effect=dispatch)
    finished, _ = execute_task(task, dispatcher=dispatcher)
    assert finished.status == 'CANCELLED'
    dispatcher.assert_called_once()


def test_confirmation_executes_exact_step_once_then_continues(monkeypatch, tmp_path):
    monkeypatch.setattr('core.action_executor.MEMORY_FILE', tmp_path/'user.json')
    monkeypatch.setattr('core.environment.pending_plan._pending', None)
    task = create_task('test', [{'action':'CLOSE_APPLICATION', 'target':'firefox'}, {'action':'GET_TIME'}])
    dispatcher = Mock(return_value=(True, 'ok'))
    task, _ = execute_task(task, dispatcher=dispatcher)
    assert task.status == 'WAITING_CONFIRMATION'
    assert get_pending()['action']['target'] == 'firefox'
    dispatcher.assert_not_called()
    assert 'COMPLETED' in handle_message('confirme', dispatcher=dispatcher)
    assert dispatcher.call_count == 2
    assert get_pending() is None
    handle_message('confirme', dispatcher=dispatcher)
    assert dispatcher.call_count == 2


def test_unknown_inflight_result_is_not_replayed(monkeypatch):
    from core.state_store import get_store
    task = create_task('test', [{'action':'GET_TIME'}])
    get_store().mutate('tasks',task.id,lambda v:{**v,'in_flight':True,'status':'RUNNING'})
    dispatcher = Mock()
    task, _ = execute_task(task, dispatcher=dispatcher)
    assert task.status == 'PAUSED'
    assert 'inconnu' in task.error
    dispatcher.assert_not_called()


def test_agent_observes_result_before_next_step(monkeypatch, tmp_path):
    monkeypatch.setattr('core.action_executor.MEMORY_FILE', tmp_path/'user.json')
    observations = []
    def next_action(goal, results):
        observations.append([dict(r) for r in results])
        return {'action':'GET_TIME'} if not results else None
    monkeypatch.setattr('core.tool_agent.next_action', next_action)
    task = create_task('donne l’heure', steps=[], agent=True)
    task, _ = execute_task(task, dispatcher=Mock(return_value=(True,'12:00')))
    assert task.status == 'COMPLETED'
    assert observations[0] == []
    assert observations[1][0]['message'] == '12:00'


def test_cancellation_during_model_call_prevents_action(monkeypatch):
    task = create_task('mission', steps=[], agent=True)
    def proposal(*_):
        cancel_task(task.id)
        return {'action': 'GET_TIME'}
    monkeypatch.setattr('core.tool_agent.next_action', proposal)
    dispatcher = Mock()
    result, _ = execute_task(task, dispatcher=dispatcher)
    assert result.status == 'CANCELLED'
    dispatcher.assert_not_called()


def test_replaced_confirmation_can_be_recovered(monkeypatch, tmp_path):
    from core.pending_action import set_pending
    monkeypatch.setattr('core.action_executor.MEMORY_FILE', tmp_path/'user.json')
    task = create_task('fermer', [{'action': 'CLOSE_APPLICATION', 'target': 'firefox'}])
    execute_task(task, dispatcher=Mock())
    set_pending({'action': 'CLOSE_APPLICATION', 'target': 'chrome'})
    assert load_task(task.id).status == 'PAUSED'


def test_composed_commands_are_resumable_through_orchestrator(monkeypatch, tmp_path):
    from core import orchestrator
    monkeypatch.setattr('core.action_executor.MEMORY_FILE', tmp_path/'user.json')
    monkeypatch.setattr('core.environment.pending_plan._pending', None)
    monkeypatch.setattr(orchestrator, 'build_decision_context', lambda _: {})
    monkeypatch.setattr(orchestrator, 'get_personal_context', lambda: {})
    dispatcher = Mock(return_value=(True, 'ok'))
    monkeypatch.setattr(orchestrator, 'dispatch', dispatcher)
    response = orchestrator.process('ouvre chrome puis ferme firefox puis quelle heure est-il')
    assert 'Confirmer' in response
    assert dispatcher.call_count == 1
    assert 'COMPLETED' in handle_message('confirme', dispatcher=dispatcher)
    assert dispatcher.call_count == 3


def test_personal_work_routine_preserves_targets():
    assert 'enregistrée' in handle_message('configure ma routine de travail : ouvre firefox puis ouvre github')
    task = create_task('au boulot')
    assert task.steps == [{'action': 'OPEN_APPLICATION', 'target': 'firefox'}, {'action': 'OPEN_URL', 'url': 'https://github.com'}]
