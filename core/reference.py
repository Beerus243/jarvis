from core.conversation import get_context
from memory.text_normalizer import normalize_text


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

    if not has_reference(message):

        return message


    previous_subject = get_previous_subject()

    if not previous_subject:

        return message


    return (
        f"Contexte précédent : {previous_subject}\n"
        f"Nouvelle question : {message}"
    )