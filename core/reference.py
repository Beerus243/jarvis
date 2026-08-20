from core.conversation import get_context
from memory.text_normalizer import normalize_text
import re


REFERENCES = [
    "il",
    "elle",
    "lui",
    "ça",
    "cela",
    "ce projet",
    "cette application",
    "ce programme",
    "ce logiciel",
    "cet objectif",
]

_TARGETS = {
    "serveur": ("backend", "quelle technologie gère mon serveur"),
    "backend": ("backend", "quelle technologie gère mon serveur"),
    "frontend": ("frontend", "quelle technologie utilise mon interface"),
    "interface": ("frontend", "quelle technologie utilise mon interface"),
    "base": ("base_de_donnees", "où sont stockées les données"),
    "donnees": ("base_de_donnees", "où sont stockées les données"),
    "langage": ("langage", "avec quel langage ai-je développé le projet"),
    "technologie": (None, None),
}


def has_reference(message):

    message = normalize_text(message)

    words = message.split()

    references_simples = [
        "il",
        "elle",
        "lui",
        "ça",
        "cela",
    ]

    for reference in references_simples:

        if reference in words:
            return True

    references_composes = [
        "ce projet",
        "cette application",
        "ce programme",
        "ce logiciel",
        "cet objectif",
    ]

    for reference in references_composes:

        if reference in message:
            return True

    return False


def get_previous_subject():

    context = get_context()

    if not context:
        return None

    for message in reversed(context):

        if message.get("role") != "user":
            continue

        content = message.get("message", "").strip()

        if content:
            return content

    return None


def resolve_reference(message):

    # --------------------------------------------------------
    # Si la phrase ne contient pas de référence,
    # inutile de chercher un contexte.
    # --------------------------------------------------------

    if not has_reference(message) and not _is_elliptical(message):

        return message


    previous_subject = get_previous_subject()

    if not previous_subject:

        return message


    return (
        f"Contexte précédent : {previous_subject}\n"
        f"Nouvelle question : {message}"
    )


def _is_elliptical(message):
    text = normalize_text(message)
    return text.startswith("et ") or any(
        phrase in text
        for phrase in (
            "celui dont on parlait",
            "ce dont je parlais",
            "comme je t ai dit",
            "cette technologie",
        )
    )


def _target_from_text(text):
    for word, (target, query) in _TARGETS.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            return target, query
    return None, None


def analyze_reference(message, context=None):
    """Retourne une résolution structurée sans inventer de cible."""
    text = normalize_text(message)
    has_context = context is not None
    context = context or {}
    if has_context:
        previous = context.get("previous_user_message")
    else:
        previous = get_previous_subject()
    target, query = _target_from_text(text)

    if target:
        return {"resolved": True, "type": "project", "target": target,
                "source": "message", "confidence": 0.95, "query": query}

    if not _is_elliptical(message):
        return {"resolved": False, "type": None, "target": None,
                "source": None, "confidence": 1.0, "query": None}

    previous_target, previous_query = _target_from_text(normalize_text(previous or ""))
    if previous_target:
        return {"resolved": True, "type": "project", "target": previous_target,
                "source": "conversation", "confidence": 0.85,
                "query": previous_query}

    if previous:
        return {"resolved": True, "type": "conversation", "target": None,
                "source": "conversation", "confidence": 0.35, "query": None}

    return {"resolved": False, "type": None, "target": None,
            "source": None, "confidence": 0.30, "query": None}
