from core.environment.intent import detect_environment_intent
from core.environment.command_handler import handle_environment_intent
from core.environment.pending_plan import clear_pending, get_pending

def test_confirmation_without_plan_is_safe():
    clear_pending()
    assert "Aucun plan" in handle_environment_intent(detect_environment_intent("oui"))

def test_plan_confirmation_is_bound_and_cleared():
    clear_pending()
    plan = detect_environment_intent("prépare mon environnement Android")
    response = handle_environment_intent(plan)
    assert get_pending() is not None and "ENV-" in response
    confirmation = handle_environment_intent(detect_environment_intent("oui"))
    assert "aucun artefact" in confirmation.lower() and get_pending() is None

def test_cancel_clears_pending_plan():
    clear_pending(); handle_environment_intent(detect_environment_intent("prépare mon environnement Android"))
    assert "annulé" in handle_environment_intent(detect_environment_intent("annule")).lower()
