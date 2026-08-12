from conversation import get_context


REFERENCES = [
    "il",
    "elle",
    "lui",
    "elle",
    "ça",
    "cela",
    "ce projet",
    "cette application",
    "ce programme",
    "ce logiciel",
    "cet objectif",
]


def has_reference(message):

    message = message.lower()

    for reference in REFERENCES:

        if reference in message:
            return True

    return False


def get_previous_subject():

    context = get_context()

    if not context:
        return None

    # On parcourt les derniers messages
    # du plus récent au plus ancien

    for message in reversed(context):

        content = message.get("content", "")

        if not content:
            continue

        # Pour l'instant on récupère simplement
        # le dernier message utilisateur pertinent

        if message.get("role") == "user":

            return content

    return None

def resolve_reference(message):

    previous_subject = get_previous_subject()

    if not previous_subject:
        return message

    message_lower = message.lower()

    references = [
        "il",
        "elle",
        "lui",
        "ça",
        "cela",
        "ce projet",
        "cette application",
        "ce programme",
        "ce logiciel"
    ]

    has_ref = any(
        ref in message_lower
        for ref in references
    )

    if not has_ref:
        return message

    return (
        f"Contexte précédent : {previous_subject}\n"
        f"Nouvelle question : {message}"
    )