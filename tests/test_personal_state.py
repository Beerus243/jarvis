import json
from datetime import datetime, timezone

from memory import personal_state
from core.orchestrator import process


def memory_file(tmp_path, monkeypatch):
    path = tmp_path / "user.json"
    path.write_text(json.dumps({"name": "Fabrice"}), encoding="utf-8")
    monkeypatch.setattr(personal_state, "MEMORY_FILE", path)
    return path


def test_sleeping_state(tmp_path, monkeypatch):
    path = memory_file(tmp_path, monkeypatch)
    assert "dors" in personal_state.update_personal_state("Je vais dormir")
    assert json.loads(path.read_text())["personal_state"]["activity"] == "sleeping"


def test_start_sleeping(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 20, 0, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je vais dormir", now=started)
    state = personal_state.get_personal_state()
    assert state["activity"] == "sleeping"
    assert state["availability"] == "unavailable"
    assert state["started_at"] == started.isoformat()


def test_wake_up(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais dormir")
    personal_state.update_personal_state("Je me réveille")
    state = personal_state.get_personal_state()
    assert state["activity"] == "awake"
    assert state["availability"] == "available"
    assert state["location"] == "home"


def test_eating_state(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais manger")
    assert personal_state.get_personal_state()["activity"] == "eating"


def test_eating_phrasing():
    for phrase in (
        "Je vais déjeuner",
        "Je vais prendre mon petit-déjeuner",
        "Je pars manger",
        "Je suis en train de manger",
        "Je mange",
    ):
        assert personal_state.detect_personal_state(phrase)["activity"] == "eating"


def test_eating_question(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je mange")
    assert personal_state.answer_personal_state_question("Est-ce que je mange actuellement ?") == "Oui, tu manges actuellement."
    assert personal_state.answer_personal_state_question("Je suis en train de manger ?") == "Oui, tu manges actuellement."


def test_eating_duration(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
    now = datetime(2026, 8, 22, 12, 25, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je vais manger", now=started)
    assert personal_state.answer_personal_state_question("Je mange depuis combien de temps ?", now=now) == "Tu manges depuis environ 25 minutes."


def test_finished_eating(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je mange")
    assert "fini de manger" in personal_state.update_personal_state("J'ai fini de manger")
    assert personal_state.get_personal_state()["activity"] == "awake"


def test_not_eating(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais travailler")
    assert personal_state.answer_personal_state_question("Depuis quand je mange ?") == "Tu ne manges pas actuellement."


def test_general_food_question_is_not_eating_state():
    assert personal_state.detect_personal_state("Pourquoi les humains mangent ?") is None
    assert personal_state.detect_personal_state("Pourquoi doit-on manger ?") is None
    assert personal_state.detect_personal_state("Qu'est-ce qu'on mange habituellement ?") is None
    assert personal_state.detect_personal_state("J'aime manger du riz.") is None


def test_eating_question_does_not_call_groq(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais manger")
    monkeypatch.setattr("core.orchestrator._ai_fallback", lambda *args: (_ for _ in ()).throw(AssertionError("Groq appelé")))
    assert process("Je mange depuis combien de temps ?").startswith("Tu manges depuis environ")


def test_working_state(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais travailler")
    assert personal_state.get_personal_state()["activity"] == "working"


def test_outside_state(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais sortir")
    state = personal_state.get_personal_state()
    assert state["activity"] == "outside"
    assert state["location"] == "outside"


def test_home_state(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je suis rentré")
    assert personal_state.get_personal_state()["location"] == "home"


def test_availability(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je suis disponible")
    assert personal_state.get_personal_state()["availability"] == "available"
    assert "disponible" in personal_state.answer_personal_state_question("Suis-je disponible ?")


def test_state_question(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais étudier")
    assert personal_state.answer_personal_state_question("Qu'est-ce que je fais actuellement ?") == "Tu étudies actuellement."


def test_sleeping_question(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais dormir")
    assert personal_state.answer_personal_state_question("Est-ce que je dors actuellement ?") == "Oui, tu dors actuellement."


def test_sleep_duration(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 20, 0, tzinfo=timezone.utc)
    now = datetime(2026, 8, 22, 22, 15, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je vais dormir", now=started)
    answer = personal_state.answer_personal_state_question("Je dors depuis combien de temps ?", now=now)
    assert answer == "Tu dors depuis environ 2 heures et 15 minutes."


def test_not_sleeping(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais travailler")
    assert personal_state.answer_personal_state_question("Depuis quand je dors ?") == "Tu ne dors pas actuellement."


def test_sleep_phrasing():
    for phrase in ("je vais faire dodo", "je vais au lit", "je suis en train de dormir"):
        assert personal_state.detect_personal_state(phrase)["activity"] == "sleeping"


def test_wake_phrasing():
    for phrase in ("je viens de me réveiller", "je suis réveillé maintenant"):
        assert personal_state.detect_personal_state(phrase)["activity"] == "awake"


def test_sleep_question_does_not_change_state(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    assert personal_state.detect_personal_state("Pourquoi les humains dorment ?") is None
    assert personal_state.detect_personal_state("Je dors depuis combien de temps ?") is None


def test_sleep_question_does_not_call_groq(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 20, 0, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je vais dormir", now=started)
    monkeypatch.setattr("core.orchestrator._ai_fallback", lambda *args: (_ for _ in ()).throw(AssertionError("Groq appelé")))
    assert process("Depuis quand je dors ?").startswith("Tu dors depuis environ")


def test_state_is_local(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais travailler")
    result = process("Qu'est-ce que je fais actuellement ?")
    assert result == "Tu travailles actuellement."


def test_state_question_never_calls_groq(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais travailler")
    monkeypatch.setattr("core.orchestrator._ai_fallback", lambda *args: (_ for _ in ()).throw(AssertionError("Groq appelé")))
    assert process("Suis-je disponible ?") == "Non, tu es actuellement occupé."
