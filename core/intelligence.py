"""Décision locale de JARVIS, sans exécution ni appel réseau."""

from core.intent import detect_intent
from core.reference import has_reference, analyze_reference
from memory.personal_memory import detect_personal_question
from memory.personal_state import detect_personal_state, detect_personal_state_question
from memory.project_questions import detect_project_question
from memory.project_parser import parse_project_information
from core.action_policy import detect_sensitive_request
from memory.text_normalizer import normalize_text
from core.pc_context import answer_pc_question
from core.task_engine import get_active_task

CONFIDENCE_HIGH = 0.90
CONFIDENCE_CONTEXT = 0.70
CONFIDENCE_LOW = 0.30


def _decision(decision_type, intent=None, confidence=0.50,
              requires_memory=False, requires_ai=False, uses_context=False,
              ambiguous=False):
    return {
        "type": decision_type,
        "intent": intent,
        "confidence": confidence,
        "requires_memory": requires_memory,
        "requires_ai": requires_ai,
        "uses_context": uses_context,
        "ambiguous": ambiguous,
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
    normalized = normalize_text(message)
    contextual_text = normalized.rstrip(" ?!.")
    contextual_phrases = (
        "pourquoi",
        "comment",
        "et pourquoi",
        "et comment",
        "et lui",
        "et ca",
        "et ça",
        "et cela",
        "et celui la",
        "lequel",
        "laquelle",
        "ensuite",
        "et apres",
    )
    is_contextual = (
        contextual_text in contextual_phrases
        or contextual_text.startswith("et pourquoi")
        or contextual_text.startswith("et comment")
        or contextual_text.startswith("pourquoi ")
        or contextual_text.startswith("comment ")
    )

    intent = detect_intent(message)
    if intent:
        return _decision("ACTION", intent, 0.98)

    if normalized in {"annule", "annuler", "stop", "arrête", "arrete"} and get_active_task():
        return _decision("TASK", "CANCEL", 0.99)
    if "prépare mon environnement de travail" in normalized or "prepare mon environnement de travail" in normalized:
        return _decision("TASK", "CREATE", 0.99)

    sensitive_action = detect_sensitive_request(message)
    if sensitive_action:
        return _decision("ACTION", sensitive_action, 0.99)

    if parse_project_information(message):
        return _decision(
            "PROJECT_MEMORY",
            "UPDATE",
            0.99,
            requires_memory=True,
        )

    if detect_personal_state(message):
        return _decision("PERSONAL_STATE", "UPDATE", 0.99, requires_memory=True)

    if detect_personal_state_question(message):
        return _decision("PERSONAL_STATE", "QUESTION", 0.99, requires_memory=True)

    if detect_personal_question(message):
        return _decision(
            "PERSONAL_MEMORY",
            _personal_intent(message),
            0.99,
            requires_memory=True,
        )

    if answer_pc_question(message, context.get("pc_context")):
        return _decision("PC_CONTEXT", "QUESTION", 0.99, uses_context=True)

    project_intent = detect_project_question(message)
    if project_intent:
        reference_confidence = reference.get("confidence", 0.99)
        return _decision(
            "PROJECT_MEMORY",
            project_intent,
            reference_confidence if normalized.startswith("et ") else 0.99,
            requires_memory=True,
            uses_context=normalized.startswith("et "),
            ambiguous=reference_confidence < CONFIDENCE_CONTEXT,
        )

    if reference.get("resolved") and reference.get("target"):
        target = reference["target"]
        if target in {"backend", "frontend", "base_de_donnees", "langage"} \
                and reference.get("source") == "message":
            return _decision(
                "PROJECT_MEMORY", target, reference["confidence"], True,
                ambiguous=reference["confidence"] < CONFIDENCE_CONTEXT,
            )

    if normalize_text(message).find("prenom") >= 0 and context.get("previous_user_message"):
        return _decision("PERSONAL_MEMORY", "IDENTITY", 0.85, True)

    previous_user = context.get("previous_user_message")
    is_short_follow_up = normalized.startswith("et ") and previous_user
    if (has_reference(message) or is_short_follow_up or is_contextual) and previous_user:
        confidence = reference.get("confidence", CONFIDENCE_CONTEXT)
        return _decision(
            "CONTEXT",
            confidence=confidence,
            requires_memory=True,
            uses_context=True,
            ambiguous=confidence < CONFIDENCE_CONTEXT,
        )

    fallback_confidence = (
        reference.get("confidence", 0.50)
        if is_contextual and reference.get("confidence", 1.0) < 1.0
        else 0.50
    )
    return _decision(
        "GENERAL_AI",
        confidence=fallback_confidence,
        requires_memory=True,
        requires_ai=True,
        ambiguous=fallback_confidence < CONFIDENCE_CONTEXT,
    )
