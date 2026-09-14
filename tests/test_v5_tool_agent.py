from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from core.tool_agent import next_action, validate_action, TOOLS
from core.action_policy import classify_action, BLOCKED_ACTION


def test_every_mission_tool_has_execution_policy():
    assert all(classify_action(action) != BLOCKED_ACTION for action in TOOLS)


@pytest.mark.parametrize('action', [
    {'action': 'RUN_COMMAND', 'command': 'anything'},
    {'action': 'GET_TIME', 'unexpected': 'value'},
    {'action': 'OPEN_URL', 'url': 'file:///etc/passwd'},
    {'action': 'OPEN_APPLICATION', 'target': 'unknown'},
])
def test_invalid_model_tool_is_rejected(action):
    with pytest.raises(ValueError):
        validate_action(action)


def test_tool_call_is_parsed_without_execution(monkeypatch):
    monkeypatch.setattr('memory.service.relevant_context', lambda _: 'mémoire')
    call = SimpleNamespace(function=SimpleNamespace(name='GET_TIME', arguments='{}'))
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[call]))])
    assert next_action('heure', [], client=client) == {'action': 'GET_TIME'}
    args = client.chat.completions.create.call_args.kwargs
    assert args['timeout'] == 20 and args['tools']
    client.chat.completions.create.return_value.choices[0].message.tool_calls = [call, call]
    with pytest.raises(ValueError, match='seule action'):
        next_action('heure', [], client=client)
