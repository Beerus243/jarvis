"""Chaque test dispose de son état durable ; aucun rappel réel n'est consommé."""
import pytest


@pytest.fixture(autouse=True)
def isolated_runtime_state(monkeypatch, tmp_path):
    monkeypatch.setenv('JARVIS_STATE_DB', str(tmp_path / 'runtime.sqlite3'))
    # Les plans d'environnement restent en mémoire et doivent aussi être
    # isolés : un ancien plan ne doit pas rendre une confirmation PC ambiguë.
    monkeypatch.setattr('core.environment.pending_plan._pending', None)


@pytest.fixture(autouse=True)
def no_real_environment_downloads(monkeypatch):
    def offline(_url):
        raise OSError('offline test fixture')
    monkeypatch.setattr('core.environment.conversation_plan.fetch_metadata', offline)
