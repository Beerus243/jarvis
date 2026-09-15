from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from core.proactivity import model, projects
from core.proactivity.engine import PersonalAgent
from core.proactivity.commands import handle_personal_command
from core.state_store import get_store
from core.runtime import Runtime


@pytest.fixture
def setup(monkeypatch, tmp_path):
    root = tmp_path / 'Menu2kin'
    root.mkdir()
    project = {'key': 'menu2kin', 'name': 'Menu2kin', 'path': str(root)}
    monkeypatch.setattr(projects, 'registered', lambda: [project])
    clock = SimpleNamespace(wall=1800000000., mono=100.)
    runtime = Runtime()
    agent = PersonalAgent(runtime.enqueue, clock=lambda: clock.wall, monotonic=lambda: clock.mono)
    runtime.personal_agent = agent
    monkeypatch.setattr('core.runtime._runtime', runtime)
    agent.start()
    pc = {'active_window': {'available': True, 'application': 'code', 'title': 'Menu2kin — code'}}
    def observe(seconds=0, state='active', context=None):
        clock.wall += seconds
        clock.mono += seconds
        agent.observe(pc if context is None else context, {'state': state})
    observe()
    yield SimpleNamespace(agent=agent, runtime=runtime, clock=clock, observe=observe, pc=pc, project=project)
    agent.stop()


def test_counts_only_consecutive_active_samples(setup):
    s = setup
    s.observe(15)
    assert s.agent.session['active_seconds'] == 15
    s.observe(15, 'away')
    s.observe(15)
    assert s.agent.session['active_seconds'] == 15
    s.observe(15)
    assert s.agent.session['active_seconds'] == 30


@pytest.mark.parametrize('state', ['locked', 'away', 'unknown'])
def test_inactive_samples_do_not_trigger_or_deliver(setup, state):
    setup.observe(15, state)
    setup.runtime.enqueue('reminder', 'test', reminder_id='r', now=setup.clock.wall)
    assert setup.runtime.deliver(Mock(), now=setup.clock.wall) == []
    assert setup.agent.session['active_seconds'] == 0


@pytest.mark.parametrize('gap', [46, 600, 86400])
def test_suspend_gap_not_credited(setup, gap):
    setup.observe(gap)
    assert setup.agent.session['active_seconds'] == 0


def test_wall_clock_jump_not_credited(setup):
    setup.clock.wall += 3600
    setup.observe(15)
    assert setup.agent.session['active_seconds'] == 0


def test_project_change_archives_and_invalidates_offer(setup, monkeypatch):
    setup.agent.propose()
    other = {**setup.project, 'key': 'other', 'name': 'Other'}
    monkeypatch.setattr(projects, 'registered', lambda: [setup.project, other])
    setup.observe(15, context={'active_window': {'available': True, 'application': 'code', 'title': 'Other'}})
    assert setup.agent.session['project']['key'] == 'other'
    assert not setup.agent.pending()
    assert len(get_store().get('v7', 'sessions')) == 1


def test_ambiguous_title_is_not_a_project(setup, monkeypatch):
    monkeypatch.setattr(projects, 'registered', lambda: [setup.project, {**setup.project, 'key': 'another', 'name': 'Menu2kin'}])
    assert projects.identify(setup.pc) is None


def test_sleep_persists_restart_and_prevents_reminder(setup):
    handle_personal_command('je vais dormir')
    setup.agent.stop()
    setup.agent.start()
    setup.observe(15)
    assert setup.agent.mode() == 'sleeping'
    assert not setup.agent.available(reminder=True)
    handle_personal_command('laisse passer les rappels pendant mon sommeil')
    assert setup.agent.available(reminder=True)
    handle_personal_command('je suis réveillé')
    assert setup.agent.mode() == 'auto'


def test_focus_allows_reminders_only(setup):
    handle_personal_command('mode concentration')
    assert setup.agent.available(reminder=True)
    assert not setup.agent.available()


def test_restart_never_replays_confirmation_or_counts_downtime(setup):
    setup.observe(15)
    setup.agent.propose()
    setup.clock.wall += 5000
    setup.agent.start()
    assert setup.agent.feedback('accept') == 'Aucune proposition personnelle en attente.'
    setup.observe()
    assert setup.agent.session['active_seconds'] == 0


def test_proposal_expires_and_silence_does_not_confirm(setup):
    setup.agent.propose()
    setup.clock.wall += 301
    assert not setup.agent.pending()
    assert not get_store().items('v7_checkpoints')


def test_break_plan_creates_verified_checkpoint_once(setup):
    setup.observe(15)
    assert 'fichiers' in handle_personal_command('prépare ma pause')
    assert 'vérifié' in handle_personal_command('confirme ma proposition')
    assert setup.agent.mode() == 'break'
    assert len(get_store().items('v7_checkpoints')) == 1
    assert 'Aucune' in handle_personal_command('confirme ma proposition')
    point = get_store().items('v7_checkpoints')[0][1]
    assert point['editor_files_saved'] is False
    assert 'Menu2kin' in handle_personal_command('reprends mon projet')
    assert setup.agent.mode() == 'auto'


def test_changed_path_blocks_prepared_action(setup, monkeypatch):
    setup.agent.propose()
    monkeypatch.setattr(projects, 'registered', lambda: [{**setup.project, 'path': '/missing'}])
    assert 'chemin' in setup.agent.feedback('accept')
    assert not get_store().items('v7_checkpoints')


def test_unavailable_context_blocks_confirmation(setup):
    setup.agent.propose()
    setup.observe(15, 'locked')
    assert 'indisponible' in setup.agent.feedback('accept')
    assert not get_store().items('v7_checkpoints')


def test_bare_confirmation_does_not_reach_another_pending_action(setup):
    setup.agent.propose()
    assert 'confirme ma proposition' in handle_personal_command('oui')
    assert not get_store().items('v7_checkpoints')
    from core.command_session import is_exit_command
    assert not is_exit_command('stop')


def test_question_budget_and_unanswered_episode(setup):
    for _ in range(40):
        setup.observe(15)
    assert setup.agent.offer['kind'] == 'preference'
    assert setup.agent.offer['state'] == 'QUEUED'
    setup.clock.wall += 3600
    setup.observe(15)
    assert not setup.agent.pending()
    assert get_store().get('v7', 'budget')['questions'] == 1


def test_unknown_question_requires_numeric_answer(setup):
    setup.agent.propose('preference')
    assert '60 minutes' in setup.agent.feedback('accept')
    assert model.preference('break_minutes') is None
    assert '45' in handle_personal_command('ma pause après 45 minutes')
    assert model.preference('break_minutes') == 45
    assert not setup.agent.pending()


@pytest.mark.parametrize('minutes', [0, 4, 241, 10000])
def test_invalid_preferences_rejected(setup, minutes):
    assert '5 à 240' in handle_personal_command(f'ma pause après {minutes} minutes')
    assert model.preference('break_minutes') is None


def test_habit_needs_three_days_and_confirmation(setup):
    for day in range(3):
        model.observe_break(str(day), 3600, now=setup.clock.wall + day * 86400)
    assert model.preference('break_minutes') is None
    assert get_store().get('v7', 'break_hypothesis')['value'] == 60
    setup.clock.wall += 2 * 86400
    setup.agent.propose('preference')
    setup.agent.feedback('accept')
    assert model.preference('break_minutes') == 60


def test_repeated_pauses_same_day_do_not_infer_habit(setup):
    for i in range(5):
        model.observe_break(str(i), 3600, now=setup.clock.wall)
    assert get_store().get('v7', 'break_hypothesis') is None


def test_forgetting_removes_samples_and_prevents_relearning(setup):
    model.confirm('break_minutes', 60)
    model.observe_break('1', 3600, now=setup.clock.wall)
    handle_personal_command('oublie mon rythme de pause')
    model.observe_break('2', 3600, now=setup.clock.wall)
    assert model.preference('break_minutes') is None
    assert not get_store().get('v7', 'break_samples')


def test_decline_and_deferral(setup):
    setup.agent.propose()
    assert '15' in setup.agent.feedback('defer', 15)
    setup.observe(600)
    assert setup.agent.offer['state'] == 'DEFERRED'
    setup.observe(300)
    assert setup.agent.offer['state'] == 'QUEUED'
    notice = get_store().get('notifications', setup.agent.offer['notice_id'])
    assert setup.agent.can_deliver(notice)
    setup.agent.delivered(notice)
    setup.agent.feedback('refuse')
    assert not setup.agent.pending()
    assert not get_store().items('v7_checkpoints')


def test_declared_project_is_used_only_with_development_window(setup):
    assert 'déclaré' in handle_personal_command('je travaille sur Menu2kin')
    assert projects.identify({'active_window': {'available': True, 'application': 'firefox', 'title': 'Menu2kin'}}, 'menu2kin') is None


def test_automatic_delivery_records_actual_delivery(setup):
    setup.agent.propose('preference', automatic=True)
    notices = setup.runtime.deliver(lambda _: True, now=setup.clock.wall)
    assert len(notices) == 1
    assert setup.agent.offer['state'] == 'DELIVERED'


def test_failed_audio_leaves_question_unanswered_and_backs_off(setup):
    setup.agent.propose('preference', automatic=True)
    sink = Mock(return_value=False)
    setup.runtime.deliver(sink, now=setup.clock.wall)
    setup.runtime.deliver(sink, now=setup.clock.wall + 1)
    assert sink.call_count == 1
    assert setup.agent.offer['state'] == 'QUEUED'


def test_stale_presence_defers_notifications(setup):
    setup.clock.mono += 46
    assert not setup.agent.available()


def test_dont_ask_again_cancels_pending_question(setup):
    setup.agent.propose('preference', automatic=True)
    handle_personal_command('ne me pose plus de questions')
    assert not setup.agent.pending()
    assert model.preference('questions') is False


def test_commands_reach_orchestrator_without_ai(setup, monkeypatch):
    import core.orchestrator as module
    ai = Mock(side_effect=AssertionError('Personal commands must stay local'))
    monkeypatch.setattr(module, '_ai_fallback', ai)
    assert 'Préférence' in str(module.process('ma pause après 45 minutes'))
    ai.assert_not_called()


def test_stale_pc_context_does_not_count_or_offer(setup):
    setup.observe(15, context={**setup.pc, 'observed_at': setup.clock.wall - 60})
    assert setup.agent.session['active_seconds'] == 0
    assert not setup.agent.pending()


def test_spoken_interaction_counts_presence_only_when_unlocked(setup):
    setup.agent.observe(setup.pc, {'state': 'away', 'locked': False})
    setup.agent.touch()
    assert setup.agent.available()
    setup.agent.observe(setup.pc, {'state': 'locked'})
    setup.agent.touch()
    assert not setup.agent.available()


def test_configured_music_uses_known_action_after_confirmation(setup, monkeypatch):
    from core.action_executor import ActionResult
    execute = Mock(return_value=ActionResult(True, 'MEDIA_PAUSE', 'En pause'))
    monkeypatch.setattr('core.action_executor.execute_action', execute)
    handle_personal_command('ajoute la musique à ma routine de pause')
    assert 'musique' in setup.agent.propose()
    execute.assert_not_called()
    assert 'Musique' in setup.agent.feedback('accept')
    execute.assert_called_once_with({'action': 'MEDIA_PAUSE'}, confirmation=True)


def test_failed_pc_action_reports_partial_result(setup, monkeypatch):
    from core.action_executor import ActionResult
    monkeypatch.setattr('core.action_executor.execute_action', lambda *a, **kw: ActionResult(False, 'MEDIA_PAUSE', 'Pas de lecteur'))
    model.confirm('pause_music', True)
    setup.agent.propose()
    result = setup.agent.feedback('accept')
    assert 'échoué' in result
    assert setup.agent.mode() == 'auto'
    assert len(get_store().items('v7_checkpoints')) == 1


def test_stop_during_slow_pc_action_does_not_apply_remaining_steps(setup, monkeypatch):
    import threading
    from core.action_executor import ActionResult
    entered, release = threading.Event(), threading.Event()
    def execute(*a, **kw):
        entered.set()
        assert release.wait(3)
        return ActionResult(True, 'MEDIA_PAUSE', 'Pause')
    monkeypatch.setattr('core.action_executor.execute_action', execute)
    model.confirm('pause_music', True)
    setup.agent.propose()
    results = []
    worker = threading.Thread(target=lambda: results.append(setup.agent.feedback('accept')))
    worker.start()
    assert entered.wait(2)
    try:
        setup.agent.stop()
    finally:
        release.set()
        worker.join(3)
    assert 'interrompue' in results[0]
    assert setup.agent.mode() == 'auto'


def test_open_checkpoint_project_routes_through_action_policy(setup, monkeypatch):
    setup.agent.propose()
    setup.agent.feedback('accept')
    execute = Mock(return_value=SimpleNamespace(message='Projet ouvert', success=True))
    monkeypatch.setattr('core.action_executor.execute_action', execute)
    assert handle_personal_command('ouvre mon projet de reprise') == 'Projet ouvert'
    execute.assert_called_once_with({'action': 'OPEN_VSCODE', 'target': setup.project['path']})


def test_music_plan_reaches_real_dispatcher_pc_route(setup, monkeypatch):
    pc_action = Mock(return_value=SimpleNamespace(success=True, message='Pause confirmée', error=None))
    monkeypatch.setattr('core.dispatcher.execute_pc_action', pc_action)
    monkeypatch.setattr('core.action_executor._log', lambda result: None)
    model.confirm('pause_music', True)
    setup.agent.propose()
    assert 'Musique' in setup.agent.feedback('accept')
    assert pc_action.call_args.args[0].action_type == 'MEDIA_PAUSE'


def test_old_hypothesis_is_not_offered(setup):
    get_store().put('v7', 'break_hypothesis', {'at': setup.clock.wall - 31*86400, 'value': 60})
    setup.agent.propose('preference')
    assert setup.agent.offer['value'] is None


def test_numeric_answer_only_applies_to_delivered_question(setup):
    assert handle_personal_command('45 minutes') is None
    setup.agent.propose('preference')
    assert '45' in handle_personal_command('45 minutes')
    assert model.preference('break_minutes') == 45


def test_explicit_habit_rejection_forgets_preference(setup):
    model.confirm('break_minutes', 60)
    assert 'oubliés' in handle_personal_command('non ce n’est pas mon habitude')
    assert model.preference('break_minutes') is None
