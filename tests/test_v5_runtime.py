from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock
import time

from core.state_store import StateStore, get_store
from core.runtime import Runtime, add_reminder
from core.session_service import handle_message


def test_store_read_modify_write_is_transactional(tmp_path):
    store = StateStore(tmp_path/'state.sqlite3')
    def increment(_):
        store.mutate('test', 'counter', lambda n: (n or 0)+1)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(increment, range(40)))
    assert store.get('test', 'counter') == 40


def test_reminder_survives_new_runtime_and_delivers_once(monkeypatch):
    monkeypatch.setattr(time, 'time', lambda: 1000)
    reminder = add_reminder('reprendre le projet', 1030)
    sink = Mock(return_value=True)
    runtime = Runtime(notify=sink, pc_provider=lambda: {}, personal_provider=lambda: {})
    runtime.tick(1031)
    Runtime(notify=sink, pc_provider=lambda: {}, personal_provider=lambda: {}).tick(1032)
    sink.assert_called_once_with('Rappel : reprendre le projet')
    assert get_store().get('reminders', reminder['id'])['status'] == 'DELIVERED'


def test_silence_and_failed_delivery_preserve_reminder(monkeypatch):
    monkeypatch.setattr(time, 'time', lambda: 1000)
    add_reminder('pause', 1001)
    store = get_store()
    store.put('settings', 'silent', True)
    sink = Mock(return_value=False)
    runtime = Runtime(notify=sink, pc_provider=lambda: {}, personal_provider=lambda: {})
    runtime.tick(1002)
    sink.assert_not_called()
    store.put('settings', 'silent', False)
    runtime.tick(1003)
    assert store.items('notifications')[0][1]['status'] == 'PENDING'
    sink.return_value = True
    runtime.tick(1004)
    assert store.items('notifications')[0][1]['status'] == 'DELIVERED'


def test_low_battery_is_one_alert_per_discharge_episode():
    from memory.pc_proactive import clear_pc_proposals
    clear_pc_proposals()
    pc = {'battery': {'level': 10, 'charging': False}}
    sink = Mock(return_value=True)
    runtime = Runtime(notify=sink, pc_provider=lambda: pc, personal_provider=lambda: {})
    runtime.tick(10000)
    runtime.tick(14000)
    sink.assert_called_once()
    pc['battery']['charging'] = True
    runtime.tick(15000)
    pc['battery']['charging'] = False
    runtime.tick(18000)
    assert sink.call_count == 2


def test_cancelled_overdue_reminder_is_never_delivered(monkeypatch):
    monkeypatch.setattr(time, 'time', lambda: 1000)
    reminder = add_reminder('pause', 1001)
    runtime = Runtime(pc_provider=lambda: {}, personal_provider=lambda: {})
    runtime.tick(1002)
    handle_message('annule le rappel '+reminder['id'])
    sink = Mock()
    runtime.deliver(sink, now=1003)
    sink.assert_not_called()


def test_french_reminder_dialogue(monkeypatch):
    monkeypatch.setattr(time, 'time', lambda: 1000)
    assert 'enregistré' in handle_message('rappelle-moi dans deux minutes de boire de l’eau')
    reminder = get_store().items('reminders')[0][1]
    assert reminder['due_at'] == 1120
    assert reminder['message'] == 'boire de l’eau'
    assert 'boire' in handle_message('liste mes rappels')


def test_live_runtime_delivers_without_user_input(monkeypatch, tmp_path):
    from threading import Event
    from core.task_engine import create_task, load_task
    monkeypatch.setattr('core.action_executor.MEMORY_FILE', tmp_path/'user.json')
    delivered = Event()
    dispatcher = Mock(return_value=(True, '12:00'))
    runtime = Runtime(notify=lambda _: delivered.set(), pc_provider=lambda: {}, personal_provider=lambda: {},
                      interval=.02, dispatcher=dispatcher)
    task = create_task('heure', [{'action': 'GET_TIME'}])
    runtime.start()
    try:
        runtime.submit(task.id)
        assert delivered.wait(5)
        assert load_task(task.id).status == 'COMPLETED'
        dispatcher.assert_called_once()
    finally:
        runtime.stop()


def test_only_one_runtime_per_database():
    import pytest
    first = Runtime(interval=100).start()
    try:
        with pytest.raises(RuntimeError, match='déjà'):
            Runtime(interval=100).start()
    finally:
        first.stop()
