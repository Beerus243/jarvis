from core.conversation import add_message
from core.orchestrator import process
from personality.personality import personalize
from core.decision_context import build_decision_context
from memory.personal_state import get_personal_context
from core.user_state import detect_user_state
from core.task_engine import get_active_task, task_dict

# Compatibilité avec les tests/intégrations qui remplaçaient cet ancien point
# d'injection. L'appel réel est désormais géré par l'orchestrateur.
ask_ai = None


def think(message):
    response = process(message)
    context = build_decision_context(message)
    context["personal_context"] = get_personal_context()
    context["user_state"] = detect_user_state(message)
    context["active_task"] = task_dict(get_active_task())

    # ========================================================
    # PERSONALITÉ
    # ========================================================
    #
    # La personnalité ne remplace pas une action normale.
    # Elle intervient seulement lorsqu'elle a une réaction
    # contextuelle pertinente.
    # ========================================================

    personality_response = personalize(
        message,
        response,
        context,
    )

    if personality_response:
        response = personality_response

    add_message("user", message)

    if response:
        add_message("assistant", response)

    return response
