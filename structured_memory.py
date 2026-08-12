import json
from text_normalizer import normalize_text
MEMORY_FILE = "user.json"


def load_memory():

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return {}


def save_memory(user):

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            user,
            f,
            indent=4,
            ensure_ascii=False
        )


def get_project():

    user = load_memory()

    structured = user.get(
        "structured_memory",
        {}
    )

    return structured.get(
        "projet",
        {}
    )

def update_project(attribute, value):

    user = load_memory()

    if "structured_memory" not in user:

        user["structured_memory"] = {}

    if "projet" not in user["structured_memory"]:

        user["structured_memory"]["projet"] = {}

    user["structured_memory"]["projet"][attribute] = value

    save_memory(user)

def get_project_attribute(attribute):

    project = get_project()

    return project.get(attribute)

# ============================================================
# ANALYSER LES INFORMATIONS DU PROJET
# ============================================================

def analyze_project_information(message):

    text = normalize_text(message)

    # --------------------------------------------------------
    # LANGAGE
    # --------------------------------------------------------

    if (
    "développé en" in text
    or "développe en" in text
    or "développer en" in text
    or "developpé en" in text
    or "developpe en" in text
    or "developper en" in text
):

        if "python" in text:

            update_project(
                "langage",
                "Python"
            )

            return (
                "J'ai enregistré que le projet "
                "est développé en Python."
            )

        if "javascript" in text:

            update_project(
                "langage",
                "JavaScript"
            )

            return (
                "J'ai enregistré que le projet "
                "est développé en JavaScript."
            )

        if "typescript" in text:

            update_project(
                "langage",
                "TypeScript"
            )

            return (
                "J'ai enregistré que le projet "
                "est développé en TypeScript."
            )


    # --------------------------------------------------------
    # BASE DE DONNÉES
    # --------------------------------------------------------

    if (
        "base de données" in text
        or "base de donnée" in text
    ):

        if (
            "postgresql" in text
            or "postgres" in text
        ):

            update_project(
                "base_de_donnees",
                "PostgreSQL"
            )

            return (
                "J'ai enregistré que le projet "
                "utilise PostgreSQL."
            )

        if "mysql" in text:

            update_project(
                "base_de_donnees",
                "MySQL"
            )

            return (
                "J'ai enregistré que le projet "
                "utilise MySQL."
            )

        if (
            "mongodb" in text
            or "mongo" in text
        ):

            update_project(
                "base_de_donnees",
                "MongoDB"
            )

            return (
                "J'ai enregistré que le projet "
                "utilise MongoDB."
            )


    # --------------------------------------------------------
    # TYPE DU PROJET
    # --------------------------------------------------------

    if (
        "assistant ia" in text
        or "assistant intelligent" in text
    ):

        update_project(
            "type",
            "assistant IA"
        )

        return (
            "J'ai enregistré que JARVIS "
            "est un assistant IA."
        )


    return None