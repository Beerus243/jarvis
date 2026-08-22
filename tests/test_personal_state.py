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


def test_outside_question_does_not_call_groq(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais sortir")
    monkeypatch.setattr("core.orchestrator._ai_fallback", lambda *args: (_ for _ in ()).throw(AssertionError("Groq appelé")))
    assert process("Où suis-je actuellement ?") == "Tu es actuellement dehors."


def test_general_exit_question_is_not_outside():
    for phrase in (
        "Pourquoi les gens sortent ?",
        "Je préfère sortir le soir.",
        "Est-ce que tu peux m'expliquer comment sortir d'un programme ?",
        "Je veux sortir de cette application.",
    ):
        assert personal_state.detect_personal_state(phrase) is None


def test_specific_activity_has_priority():
    state = personal_state.detect_personal_state("Je vais sortir travailler")
    assert state["activity"] == "working"
    assert state["location"] == "outside"


def test_outside_question_when_home(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je suis à la maison")
    assert personal_state.answer_personal_state_question("Est-ce que je suis dehors ?") == "Tu n'es pas actuellement dehors."


def test_working_state(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais travailler")
    assert personal_state.get_personal_state()["activity"] == "working"


def test_start_working(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 8, 0, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je commence à travailler", now=started)
    state = personal_state.get_personal_state()
    assert state["activity"] == "working"
    assert state["availability"] == "busy"
    assert state["started_at"] == started.isoformat()


def test_start_studying(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je commence à étudier")
    assert personal_state.get_personal_state()["activity"] == "studying"


def test_stop_working(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je travaille")
    assert "fini de travailler" in personal_state.update_personal_state("J'ai fini de travailler")
    assert personal_state.get_personal_state()["activity"] == "awake"


def test_stop_studying(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("J'étudie")
    assert "fini d'étudier" in personal_state.update_personal_state("J'ai fini d'étudier")
    assert personal_state.get_personal_state()["activity"] == "awake"


def test_working_question(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je travaille")
    assert personal_state.answer_personal_state_question("Est-ce que je travaille ?") == "Oui, tu travailles actuellement."


def test_studying_question(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("J'étudie")
    assert personal_state.answer_personal_state_question("Est-ce que j'étudie ?") == "Oui, tu étudies actuellement."


def test_activity_question(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je travaille")
    assert personal_state.answer_personal_state_question("Quelle est mon activité actuelle ?") == "Tu travailles actuellement."


def test_working_duration(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 8, 0, tzinfo=timezone.utc)
    now = datetime(2026, 8, 22, 10, 30, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je travaille", now=started)
    assert personal_state.answer_personal_state_question("Depuis combien de temps je travaille ?", now=now) == "Tu travailles depuis environ 2 heures et 30 minutes."


def test_studying_duration(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 14, 0, tzinfo=timezone.utc)
    now = datetime(2026, 8, 22, 15, 10, tzinfo=timezone.utc)
    personal_state.update_personal_state("J'étudie", now=started)
    assert personal_state.answer_personal_state_question("Depuis combien de temps j'étudie ?", now=now) == "Tu étudies depuis environ 1 heure et 10 minutes."


def test_working_question_does_not_call_groq(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je travaille")
    monkeypatch.setattr("core.orchestrator._ai_fallback", lambda *args: (_ for _ in ()).throw(AssertionError("Groq appelé")))
    assert process("Est-ce que je travaille ?") == "Oui, tu travailles actuellement."


def test_specific_activity_preserved_when_outside():
    working = personal_state.detect_personal_state("Je vais sortir travailler")
    studying = personal_state.detect_personal_state("Je vais sortir étudier")
    assert working["activity"] == "working" and working["location"] == "outside"
    assert studying["activity"] == "studying" and studying["location"] == "outside"


def test_false_positive_work():
    assert personal_state.detect_personal_state("Pourquoi les gens travaillent ?") is None
    assert personal_state.detect_personal_state("Comment fonctionne le travail ?") is None
    assert personal_state.detect_personal_state("Je cherche du travail") is None
    assert personal_state.detect_personal_state("Je travaille sur un projet informatique") is None


def test_false_positive_study():
    assert personal_state.detect_personal_state("Je cherche une méthode pour étudier") is None


def test_start_playing(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je commence à jouer")
    assert personal_state.get_personal_state()["activity"] == "playing"


def test_start_watching(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je regarde un film")
    assert personal_state.get_personal_state()["activity"] == "watching"


def test_start_listening(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("J'écoute de la musique")
    assert personal_state.get_personal_state()["activity"] == "listening"


def test_stop_playing(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je joue")
    personal_state.update_personal_state("J'arrête de jouer")
    assert personal_state.get_personal_state()["activity"] == "awake"


def test_stop_watching(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je regarde un animé")
    personal_state.update_personal_state("J'ai fini l'animé")
    assert personal_state.get_personal_state()["activity"] == "awake"


def test_stop_listening(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("J'écoute de la musique")
    personal_state.update_personal_state("J'arrête la musique")
    assert personal_state.get_personal_state()["activity"] == "awake"


def test_playing_duration(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 18, 0, tzinfo=timezone.utc)
    now = datetime(2026, 8, 22, 19, 30, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je joue", now=started)
    assert personal_state.answer_personal_state_question("Depuis combien de temps je joue ?", now=now) == "Tu joues depuis environ 1 heure et 30 minutes."


def test_watching_duration(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 20, 0, tzinfo=timezone.utc)
    now = datetime(2026, 8, 22, 21, 5, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je regarde un film", now=started)
    assert personal_state.answer_personal_state_question("Depuis combien de temps je regarde ?", now=now) == "Tu regardes depuis environ 1 heure et 5 minutes."


def test_listening_duration(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 10, 0, tzinfo=timezone.utc)
    now = datetime(2026, 8, 22, 10, 45, tzinfo=timezone.utc)
    personal_state.update_personal_state("J'écoute de la musique", now=started)
    assert personal_state.answer_personal_state_question("Depuis combien de temps j'écoute de la musique ?", now=now) == "Tu écoutes de la musique depuis environ 45 minutes."


def test_playing_question_does_not_call_groq(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je joue")
    monkeypatch.setattr("core.orchestrator._ai_fallback", lambda *args: (_ for _ in ()).throw(AssertionError("Groq appelé")))
    assert process("Est-ce que je joue ?") == "Oui, tu joues actuellement."


def test_outside_playing_preserves_location(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais sortir jouer")
    state = personal_state.get_personal_state()
    assert state["activity"] == "playing" and state["location"] == "outside"


def test_outside_watching_preserves_location(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais sortir regarder un film")
    state = personal_state.get_personal_state()
    assert state["activity"] == "watching" and state["location"] == "outside"


def test_false_positive_playing():
    assert personal_state.detect_personal_state("Pourquoi les gens jouent ?") is None
    assert personal_state.detect_personal_state("Comment jouer aux échecs ?") is None


def test_false_positive_watching():
    assert personal_state.detect_personal_state("Je regarde un problème dans mon code.") is None
    assert personal_state.detect_personal_state("Je vais regarder le code.") is None


def test_false_positive_listening():
    assert personal_state.detect_personal_state("J'écoute les utilisateurs.") is None
    assert personal_state.detect_personal_state("Je veux écouter une explication.") is None


def test_play_music_action_remains_action():
    from core.intelligence import analyze

    assert analyze("Joue de la musique")["type"] == "ACTION"


def test_outside_state(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais sortir")
    state = personal_state.get_personal_state()
    assert state["activity"] == "outside"
    assert state["location"] == "outside"


def test_start_outside(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 14, 0, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je vais sortir", now=started)
    state = personal_state.get_personal_state()
    assert state["activity"] == "outside"
    assert state["availability"] == "unavailable"
    assert state["location"] == "outside"
    assert state["started_at"] == started.isoformat()


def test_return_home(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais sortir")
    personal_state.update_personal_state("Je viens de rentrer")
    state = personal_state.get_personal_state()
    assert state["activity"] == "home"
    assert state["availability"] == "available"
    assert state["location"] == "home"


def test_outside_question(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je vais sortir")
    assert personal_state.answer_personal_state_question("Est-ce que je suis dehors ?") == "Tu es actuellement dehors."
    assert personal_state.answer_personal_state_question("Où suis-je actuellement ?") == "Tu es actuellement dehors."


def test_home_question(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    personal_state.update_personal_state("Je suis à la maison")
    assert personal_state.answer_personal_state_question("Est-ce que je suis à la maison ?") == "Oui, tu es actuellement à la maison."


def test_outside_duration(tmp_path, monkeypatch):
    memory_file(tmp_path, monkeypatch)
    started = datetime(2026, 8, 22, 14, 0, tzinfo=timezone.utc)
    now = datetime(2026, 8, 22, 15, 20, tzinfo=timezone.utc)
    personal_state.update_personal_state("Je vais sortir", now=started)
    assert personal_state.answer_personal_state_question("Depuis combien de temps je suis dehors ?", now=now) == "Tu es dehors depuis environ 1 heure et 20 minutes."


def test_outside_phrasing():
    for phrase in ("Je sors", "Je vais dehors", "Je quitte la maison", "Je vais en ville", "Je suis dehors"):
        assert personal_state.detect_personal_state(phrase)["location"] == "outside"


def test_return_phrasing():
    for phrase in ("Je rentre", "Je suis rentré", "Je suis revenu", "Je suis à la maison"):
        assert personal_state.detect_personal_state(phrase)["location"] == "home"


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
