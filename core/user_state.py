"""Détection locale des états subjectifs exprimés par l'utilisateur."""

import re
import unicodedata

STATE_EXPRESSIONS = {
    "tired": {"j ai sommeil", "je suis fatigue", "je suis creve", "je suis claque", "je suis epuise", "je commence a fatiguer", "je suis ko", "j en peux plus"},
    "frustrated": {"ca ne marche pas", "encore une erreur", "j en ai marre", "je suis frustre", "je suis frustree", "je craque"},
    "confused": {"je suis perdu", "je suis perdue", "je ne comprends pas", "je comprends pas", "je suis confus", "je suis confuse"},
    "satisfied": {"je suis satisfait", "je suis satisfaite", "je suis content", "je suis contente", "ca marche", "ca fonctionne", "j ai reussi"},
}


def normalize_state_text(message):
    text = unicodedata.normalize("NFD", str(message or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^\w\s']", " ", text.replace("’", "'"))
    return " ".join(text.replace("'", " ").split())


def detect_user_state(message):
    text = normalize_state_text(message)
    for state, expressions in STATE_EXPRESSIONS.items():
        if any(text == expression or text.startswith(expression + " ") for expression in expressions):
            return {"state": state, "confidence": 0.95, "expression": text}
    return None


def detect_subjective_state(message):
    return detect_user_state(message)
