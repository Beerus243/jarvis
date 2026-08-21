from core.intelligence import analyze


def test_explicit_personal_question_has_high_confidence():
    decision = analyze("quelle est ma couleur préférée ?")
    assert decision["confidence"] >= 0.90
    assert decision["ambiguous"] is False


def test_explicit_project_question_has_high_confidence():
    decision = analyze("quelle technologie utilise mon serveur ?")
    assert decision["confidence"] >= 0.90
    assert decision["ambiguous"] is False


def test_clear_elliptical_reference_is_confident():
    decision = analyze(
        "et le frontend ?",
        context={"previous_user_message": "Quelle technologie gère mon serveur ?"},
    )
    assert decision["confidence"] >= 0.70
    assert decision["ambiguous"] is False


def test_ambiguous_reference_is_low_confidence():
    decision = analyze(
        "et lui ?",
        context={"previous_user_message": "Quelle technologie utilise mon interface ?"},
    )
    assert decision["confidence"] < 0.50
    assert decision["ambiguous"] is True


def test_reference_without_context_is_low_confidence():
    decision = analyze("et ça ?", context={})
    assert decision["confidence"] < 0.50


def test_complete_question_is_not_ambiguous():
    decision = analyze("quelle technologie utilise mon interface ?")
    assert decision["ambiguous"] is False


def test_action_has_high_confidence():
    decision = analyze("quelle heure est-il ?")
    assert decision["type"] == "ACTION"
    assert decision["confidence"] >= 0.90
