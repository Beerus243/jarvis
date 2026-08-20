"""Décision locale de JARVIS, sans exécution ni appel réseau."""

from core.intent import detect_intent
from core.reference import has_reference, get_previous_subject, analyze_reference
from memory.personal_memory import detect_personal_question
from memory.project_questions import detect_project_question
from memory.project_parser import parse_project_information
from memory.text_normalizer import normalize_text


def _decision(decision_type, intent=None, confidence=0.50,
              requires_memory=False, requires_ai=False):
    return {
        "type": decision_type,
        "intent": intent,
        "confidence": confidence,
        "requires_memory": requires_memory,
        "requires_ai": requires_ai,
    }


def _personal_intent(message):
    text = normalize_text(message)
    if any(value in text for value in ("qui suis je", "quel est mon nom", "comment je m appelle")):
        return "IDENTITY"
    if "couleur" in text:
        return "FAVORITE_COLOR"
    if any(value in text for value in ("aime regarder", "regarder quoi", "gouts")):
        return "FAVORITE_CONTENT"
    return "PERSONAL"


def analyze(message, context=None):
    """Retourne une décision structurée sans exécuter de fonctionnalité."""
    message = str(message or "").strip()
    context = context or {}
    reference = context.get("reference_info") or analyze_reference(message, context)

    intent = detect_intent(message)
    if intent:
        return _decision("ACTION", intent, 0.98)

    if parse_project_information(message):
        return _decision(
            "PROJECT_MEMORY",
            "UPDATE",
            0.99,
            requires_memory=True,
        )

    if detect_personal_question(message):
        return _decision(
            "PERSONAL_MEMORY",
            _personal_intent(message),
            0.99,
            requires_memory=True,
        )

    project_intent = detect_project_question(message)
    if project_intent:
        return _decision(
            "PROJECT_MEMORY",
            project_intent,
            0.99,
            requires_memory=True,
        )

    if reference.get("resolved") and reference.get("target"):
        target = reference["target"]
        if target in {"backend", "frontend", "base_de_donnees", "langage"} \
                and reference.get("source") == "message":
            return _decision("PROJECT_MEMORY", target, reference["confidence"], True)

    if normalize_text(message).find("prenom") >= 0 and context.get("previous_user_message"):
        return _decision("PERSONAL_MEMORY", "IDENTITY", 0.85, True)

    previous_user = (
        context.get("previous_user_message")
        if "previous_user_message" in context
        else get_previous_subject()
    )
    normalized = normalize_text(message)
    is_short_follow_up = normalized.startswith("et ") and previous_user
    if (has_reference(message) or is_short_follow_up) and previous_user:
        return _decision(
            "CONTEXT",
            confidence=0.85,
            requires_memory=True,
        )

    return _decision(
        "GENERAL_AI",
        confidence=0.50,
        requires_memory=True,
        requires_ai=True,
    )
