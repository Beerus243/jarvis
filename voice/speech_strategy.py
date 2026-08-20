"""Choix de la longueur vocale selon le type de réponse."""


def select_speech(text, kind=None):
    value = str(text or "").strip()
    if kind in {"command", "question"}:
        return value
    if kind == "error":
        return value
    return value
