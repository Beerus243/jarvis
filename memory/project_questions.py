from memory.text_normalizer import normalize_text


def detect_project_question(message):

    text = normalize_text(message)

    # ========================================================
    # LANGAGE
    # ========================================================

    langage_keywords = [
        "langage",
        "language",
        "langage de programmation",
        "programmé",
        "programme",
        "code",
        "codé",
    ]

    if any(
        keyword in text
        for keyword in langage_keywords
    ):

        return "langage"

    # ========================================================
    # BACKEND
    # ========================================================

    backend_keywords = [
        "backend",
        "back end",
        "serveur",
        "partie serveur",
        "cote serveur",
        "côté serveur",
    ]

    if any(
        keyword in text
        for keyword in backend_keywords
    ):

        return "backend"

    # ========================================================
    # FRONTEND
    # ========================================================

    frontend_keywords = [
        "frontend",
        "front end",
        "interface",
        "interface utilisateur",
        "ui",
        "partie visuelle",
        "cote client",
        "côté client",
    ]

    if any(
        keyword in text
        for keyword in frontend_keywords
    ):

        return "frontend"

    # ========================================================
    # BASE DE DONNÉES
    # ========================================================

    database_keywords = [
    "base de donnees",
    "base de donnee",
    "database",
    "bdd",
    "stockage",
    "donnees",
]

    if any(
        keyword in text
        for keyword in database_keywords
    ):

        return "base_de_donnees"

    # ========================================================
    # TYPE
    # ========================================================

    type_keywords = [
        "type de projet",
        "type du projet",
        "quel genre de projet",
        "quel genre d'application",
        "nature du projet",
    ]

    if any(
        keyword in text
        for keyword in type_keywords
    ):

        return "type"

    # ========================================================
    # STACK
    # ========================================================

    stack_keywords = [
        "stack",
        "technologies utilisées",
        "technologies utilisees",
        "technologies du projet",
        "technologies de mon projet",
    ]

    if any(
        keyword in text
        for keyword in stack_keywords
    ):

        return "stack"

    return None