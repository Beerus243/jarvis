from core.reference import analyze_reference


def test_elliptical_server_resolves_to_backend():
    result = analyze_reference(
        "et le serveur ?",
        {"previous_user_message": "Quelle technologie utilise mon interface ?"},
    )
    assert result["target"] == "backend"
    assert result["resolved"] is True


def test_elliptical_frontend_resolves_to_frontend():
    result = analyze_reference(
        "et le frontend ?",
        {"previous_user_message": "Quelle technologie gère mon serveur ?"},
    )
    assert result["target"] == "frontend"


def test_unknown_reference_is_not_invented():
    result = analyze_reference("et lui ?", {})
    assert result["resolved"] is False
    assert result["confidence"] < 0.5


def test_complete_question_ignores_history():
    result = analyze_reference(
        "quelle technologie utilise mon interface ?",
        {"previous_user_message": "Quelle technologie gère mon serveur ?"},
    )
    assert result["target"] == "frontend"
    assert result["source"] == "message"
