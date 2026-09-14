from unittest.mock import Mock, patch

from core.action_executor import ActionResult
from core.response_executor import execute
from core import orchestrator


def test_semantic_text_and_dictionary_contracts():
    for value in ('souvenir', {'contenu':'souvenir'}):
        result = execute({'source':'SEMANTIC_MEMORY'},'question', handlers={'semantic':lambda _:value})
        assert result.success and result.response == 'souvenir'


def test_refused_action_remains_refused_to_brain():
    rejected = ActionResult(False, 'CLOSE_APPLICATION', 'Confirmation nécessaire', policy='CONFIRMATION_REQUIRED')
    result = execute({'source':'ACTION', 'intent':'CLOSE_APPLICATION'}, 'ferme', handlers={'dispatch':lambda _:rejected})
    assert not result.success
    assert result.status == 'WAITING_CONFIRMATION'
    assert not result.fallback_allowed


def test_banter_does_not_swallow_a_command(monkeypatch, tmp_path):
    monkeypatch.setattr('core.action_executor.MEMORY_FILE', tmp_path/'user.json')
    monkeypatch.setattr(orchestrator,'build_decision_context',lambda _: {})
    monkeypatch.setattr(orchestrator,'get_personal_context',lambda: {})
    dispatcher = Mock(return_value=(True,'Navigateur ouvert'))
    monkeypatch.setattr(orchestrator,'dispatch',dispatcher)
    assert orchestrator.process('ouvre chrome, fais moi confiance') == 'Navigateur ouvert'
    dispatcher.assert_called_once()


def test_memory_correction_is_used_by_ai(monkeypatch, tmp_path):
    from memory.service import handle_memory_command, relevant_context
    monkeypatch.setattr('memory.service.MEMORY_FILE',tmp_path/'user.json')
    handle_memory_command('retiens éditeur : VS Code')
    handle_memory_command('corrige éditeur : Vim')
    context = relevant_context('quel est mon éditeur')
    assert 'Vim' in context and 'VS Code' not in context
    handle_memory_command('oublie éditeur')
    assert 'Vim' not in relevant_context('éditeur')


def test_ai_receives_retrieved_context(monkeypatch):
    monkeypatch.setattr('memory.service.relevant_context',lambda _: 'Éditeur : Vim')
    with patch('ai.ai.ask_ai', return_value='Vim') as ask:
        assert orchestrator._ai_fallback('mon éditeur','mon éditeur') == 'Vim'
        ask.assert_called_once_with('mon éditeur','Éditeur : Vim')


def test_personality_preserves_confirmation_result(monkeypatch):
    from core import brain
    from core.execution_result import CommandResponse
    monkeypatch.setattr(brain, 'process', lambda _: CommandResponse('Action annulée.'))
    monkeypatch.setattr(brain, 'build_decision_context', lambda _: {})
    monkeypatch.setattr(brain, 'get_personal_context', lambda: {})
    monkeypatch.setattr(brain, 'add_message', lambda *_: None)
    personality = Mock(return_value='Une blague remplacerait le résultat')
    monkeypatch.setattr(brain, 'personalize', personality)
    assert brain.think('laisse tomber') == 'Action annulée.'
    personality.assert_not_called()


def test_memory_alias_correction_and_forgetting(monkeypatch, tmp_path):
    from memory.service import handle_memory_command, relevant_context
    monkeypatch.setattr('memory.service.MEMORY_FILE', tmp_path/'user.json')
    handle_memory_command('ma couleur préférée est rouge')
    handle_memory_command('corrige couleur préférée : bleu')
    context = relevant_context('couleur')
    assert 'bleu' in context and 'rouge' not in context
    handle_memory_command('oublie ma couleur préférée')
    assert 'bleu' not in relevant_context('couleur')
