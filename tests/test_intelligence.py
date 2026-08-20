from core.intelligence import analyze


def test_action():
    decision = analyze("ouvre mon navigateur")
    assert decision["type"] == "ACTION"
    assert decision["intent"] == "OPEN_BROWSER"
    assert decision["requires_ai"] is False


def test_personal_identity():
    decision = analyze("qui suis-je")
    assert decision["type"] == "PERSONAL_MEMORY"
    assert decision["requires_ai"] is False


def test_personal_color():
    decision = analyze("quelle est ma couleur préférée")
    assert decision["type"] == "PERSONAL_MEMORY"
    assert decision["requires_ai"] is False


def test_personal_content():
    decision = analyze("qu'est-ce que j'aime regarder")
    assert decision["type"] == "PERSONAL_MEMORY"
    assert decision["requires_ai"] is False


def test_project_frontend():
    decision = analyze("quelle technologie utilise mon interface")
    assert decision["type"] == "PROJECT_MEMORY"
    assert decision["requires_ai"] is False


def test_project_backend():
    decision = analyze("quelle technologie gère mon serveur")
    assert decision["type"] == "PROJECT_MEMORY"
    assert decision["requires_ai"] is False


def test_project_language():
    decision = analyze("avec quel langage ai-je développé le projet")
    assert decision["type"] == "PROJECT_MEMORY"
    assert decision["requires_ai"] is False


def test_general_ai():
    decision = analyze("pourquoi Python est-il populaire ?")
    assert decision["type"] == "GENERAL_AI"
    assert decision["requires_ai"] is True


def test_short_follow_up_uses_context():
    decision = analyze(
        "et cela ?",
        context={"previous_user_message": "Quelle technologie utilise mon interface ?"},
    )
    assert decision["type"] == "CONTEXT"


def test_reference_follow_up_becomes_project_memory():
    decision = analyze(
        "et le serveur ?",
        context={
            "previous_user_message": "Quelle technologie utilise mon interface ?",
            "reference_info": {
                "resolved": True,
                "target": "backend",
                "confidence": 0.85,
            },
        },
    )
    assert decision["type"] == "PROJECT_MEMORY"
    assert decision["intent"] == "backend"
