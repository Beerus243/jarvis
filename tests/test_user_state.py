from core.user_state import detect_user_state
from personality.personality import PersonalityEngine, personalize
from core.intelligence import analyze
from core.response_planner import plan
from unittest.mock import patch


def test_tired_phrasings():
    for phrase in ("j'ai sommeil", "je suis fatigué", "je suis crevé", "je suis claqué", "je suis épuisé", "je commence à fatiguer", "je suis KO"):
        assert detect_user_state(phrase)["state"] == "tired"


def test_subjective_states():
    assert detect_user_state("je suis frustré")["state"] == "frustrated"
    assert detect_user_state("je suis confus")["state"] == "confused"
    assert detect_user_state("je suis satisfait")["state"] == "satisfied"


def test_normal_text_and_ambiguous_phrases_are_not_tired():
    assert detect_user_state("Je travaille sur le projet") is None
    assert detect_user_state("La fatigue est un sujet intéressant") is None


def test_personality_uses_existing_context():
    engine = PersonalityEngine()
    response = engine.respond("j'ai sommeil", context={"user_state": {"state": "tired"}, "personal_context": {"activity": "working", "duration": "2 heures"}})
    assert "2 heures" in response
    assert "pause" in response.lower()


def test_personalize_backward_compatible():
    personalize("bonjour")


def test_simple_tired_state_is_local_decision():
    decision = analyze("j'ai sommeil")
    assert decision["type"] == "USER_STATE"
    assert decision["intent"]["state"] == "tired"
    assert plan(decision)["source"] == "USER_STATE"


def test_complex_tired_sentence_keeps_ai_routing():
    decision = analyze("je suis fatigué parce que je travaille sur ce bug depuis deux heures, qu'est-ce que tu me conseilles ?")
    assert decision["type"] != "USER_STATE"


def test_sleep_duration_is_not_presented_as_work_duration():
    engine = PersonalityEngine()
    response = engine.respond("j'ai sommeil", context={"user_state": {"state": "tired"}, "personal_context": {"activity": "sleeping", "duration": "85 heures"}})
    assert "85 heures" not in response
    assert "travaille" not in response


def test_work_duration_can_be_used():
    engine = PersonalityEngine()
    response = engine.respond("j'ai sommeil", context={"user_state": {"state": "tired"}, "personal_context": {"activity": "working", "duration": "2 heures"}})
    assert "2 heures" in response
