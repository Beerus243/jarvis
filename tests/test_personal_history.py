from datetime import datetime, timezone
import json

from memory import personal_state


def setup_memory(tmp_path, monkeypatch):
    path = tmp_path / "user.json"
    path.write_text(json.dumps({"name": "Fabrice"}), encoding="utf-8")
    monkeypatch.setattr(personal_state, "MEMORY_FILE", path)


def test_history_transition_and_persistence(tmp_path, monkeypatch):
    setup_memory(tmp_path, monkeypatch)
    first = datetime(2026, 8, 22, 8, tzinfo=timezone.utc)
    second = datetime(2026, 8, 22, 10, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je travaille", now=first)
    personal_state.update_personal_state("J'étudie", now=second)
    history = personal_state.get_personal_history()
    assert history[-1]["activity"] == "working"
    assert history[-1]["ended_at"] == second.isoformat()


def test_personal_context_contains_current_and_previous(tmp_path, monkeypatch):
    setup_memory(tmp_path, monkeypatch)
    first = datetime(2026, 8, 22, 8, tzinfo=timezone.utc)
    second = datetime(2026, 8, 22, 10, tzinfo=timezone.utc)
    now = datetime(2026, 8, 22, 11, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je travaille", now=first)
    personal_state.update_personal_state("J'étudie", now=second)
    context = personal_state.get_personal_context(now=now)
    assert context["activity"] == "studying"
    assert context["previous_activity"] == "working"
    assert context["duration"] == "1 heure"


def test_history_is_bounded(tmp_path, monkeypatch):
    setup_memory(tmp_path, monkeypatch)
    for index in range(55):
        personal_state.update_personal_state("Je travaille" if index % 2 else "J'étudie")
    assert len(personal_state.get_personal_history(limit=100)) <= 50
