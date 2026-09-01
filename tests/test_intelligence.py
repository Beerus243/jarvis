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
def test_normalize_and_classify_tolerates_typo():
    from core.intelligence import normalize_and_classify
    result = normalize_and_classify("lance le navigatteur")
    assert result["intent"] == "OPEN_BROWSER"
    assert result["confidence"] >= 0.70

def test_normalize_and_classify_rejects_unrelated_text():
    from core.intelligence import normalize_and_classify
    assert normalize_and_classify("parle moi de la météo") == {}

def test_advanced_personality_response_varies():
    from personality.engine import AdvancedPersonalityEngine
    e = AdvancedPersonalityEngine(); assert len({e.select_response('OPEN_APPLICATION') for _ in range(3)}) == 3

def test_advanced_personality_serious_banter_reference():
    from personality.engine import AdvancedPersonalityEngine
    e = AdvancedPersonalityEngine(); assert e.analyze_context('urgence')['seriousness'] == 1.0
    assert e.handle_banter('Tu réfléchis trop') is None
    assert e.handle_cultural_reference('Valar Morghulis') == 'Valar Dohaeris.'

def test_self_modification_is_refused_locally():
    from core.intelligence import analyze
    assert analyze('Modifie ton code')['type'] == 'SELF_MODIFICATION_REFUSAL'

def test_suggestion_is_stored_in_data(tmp_path):
    from personality.engine import AdvancedPersonalityEngine
    engine = AdvancedPersonalityEngine(tmp_path / 'user.json')
    path = engine.suggest_improvement('précharger Firefox')
    assert path.exists() and 'précharger Firefox' in path.read_text(encoding='utf-8')

def test_python_file_action_is_denied(tmp_path):
    from core.actions import PCAction
    from core.actions.executor import execute_pc_action
    result = execute_pc_action(PCAction('FILE_CREATE', {'path': str(tmp_path / 'unsafe.py')}))
    assert not result.success and result.error == 'DENIED'
