# ============================================================
# CONTEXTE DE CONVERSATION
# ============================================================

_context = {
    "last_intent": None,
    "last_application": None,
    "last_response": None,
}


def set_context(
    intent=None,
    application=None,
    response=None
):
    """
    Met à jour le contexte courant.
    """

    if intent is not None:
        _context["last_intent"] = intent

    if application is not None:
        _context["last_application"] = application

    if response is not None:
        _context["last_response"] = response


def get_context():
    """
    Retourne le contexte actuel.
    """

    return _context.copy()


def get_last_intent():
    return _context["last_intent"]


def get_last_application():
    return _context["last_application"]


def get_last_response():
    return _context["last_response"]


def clear_context():
    """
    Réinitialise le contexte.
    """

    _context["last_intent"] = None
    _context["last_application"] = None
    _context["last_response"] = None