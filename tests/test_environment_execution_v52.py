from pathlib import Path
from types import SimpleNamespace
from core.environment.intent import detect_environment_intent
from core.environment.command_handler import handle_environment_intent
from core.environment.pending_plan import clear_pending, set_pending, get_pending

def test_confirmation_does_not_execute_without_valid_artifact():
    clear_pending(); handle_environment_intent(detect_environment_intent('prépare mon environnement Android'))
    assert 'aucun artefact' in handle_environment_intent(detect_environment_intent('oui')).lower()

def test_invalid_artifact_is_rejected_before_engine(tmp_path):
    clear_pending()
    intent = detect_environment_intent('prépare mon environnement Android')
    artifact = SimpleNamespace(destination=tmp_path, checksum=None, source=SimpleNamespace(trusted=False))
    set_pending(intent, plan=SimpleNamespace(steps=[]), artifact=artifact)
    response = handle_environment_intent(detect_environment_intent('oui'))
    assert 'PLAN_INVALIDATED' in response and get_pending() is None

def test_repair_command_is_recognized():
    assert detect_environment_intent('répare mon environnement').intent == 'ENVIRONMENT_REPAIR_PLAN'
