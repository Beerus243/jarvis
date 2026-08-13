import json

from text_normalizer import normalize_text
from project_parser import parse_project_information
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

def get_project_stack():

    project = get_project()

    if not project:
        return None

    return {
        "nom": project.get("nom"),
        "langage": project.get("langage"),
        "type": project.get("type"),
        "backend": project.get("backend"),
        "frontend": project.get("frontend"),
        "base_de_donnees": project.get(
            "base_de_donnees"
        )
    }

def get_project_stack():

    project = get_project()

    if not project:
        return None

    langage = project.get("langage")
    backend = project.get("backend")
    frontend = project.get("frontend")
    database = project.get("base_de_donnees")

    return {
        "langage": langage,
        "backend": backend,
        "frontend": frontend,
        "base_de_donnees": database
    }

def answer_project_stack():

    stack = get_project_stack()

    if not stack:
        return None

    parts = []

    if stack["langage"]:
        parts.append(
            f"{stack['langage']}"
        )

    if stack["backend"]:
        parts.append(
            f"{stack['backend']} en backend"
        )

    if stack["frontend"]:
        parts.append(
            f"{stack['frontend']} en frontend"
        )

    if stack["base_de_donnees"]:
        parts.append(
            f"{stack['base_de_donnees']} comme base de données"
        )

    if not parts:
        return None

    return (
        "La stack actuelle de JARVIS est : "
        + ", ".join(parts)
        + "."
    )

def answer_project_stack():

    stack = get_project_stack()

    if not stack:
        return None

    parts = []

    if stack["langage"]:
        parts.append(
            f"développé en {stack['langage']}"
        )

    if stack["backend"]:
        parts.append(
            f"avec {stack['backend']} en backend"
        )

    if stack["frontend"]:
        parts.append(
            f"{stack['frontend']} en frontend"
        )

    if stack["base_de_donnees"]:
        parts.append(
            f"et {stack['base_de_donnees']} comme base de données"
        )

    if not parts:
        return None

    return (
        "La stack actuelle de JARVIS est : "
        + ", ".join(parts)
        + "."
    )

def answer_project_question(message):

    text = normalize_text(message)

    project = get_project()

    if not project:
        return None

    # ========================================================
    # LANGAGE
    # ========================================================

    mots_langage = [
        "langage",
        "language",
        "langage de programmation",
        "codé",
        "code",
        "développé"
    ]

    if any(mot in text for mot in mots_langage):

        langage = project.get("langage")

        if langage:

            return (
                f"Le projet est développé en {langage}."
            )

    # ========================================================
    # BASE DE DONNÉES
    # ========================================================

    mots_database = [
        "base de données",
        "base de donnée",
        "database",
        "bdd"
    ]

    if any(mot in text for mot in mots_database):

        database = project.get(
            "base_de_donnees"
        )

        if database:

            return (
                f"Le projet utilise {database}."
            )

    return None

# ============================================================
# ANALYSER LES INFORMATIONS DU PROJET
# ============================================================

def analyze_project_information(message):

    result = parse_project_information(message)

    if not result:
        return None

    attribute = result["attribute"]
    value = result["value"]

    update_project(
        attribute,
        value
    )

    if attribute == "langage":

        return (
            f"J'ai enregistré que le projet "
            f"est développé en {value}."
        )

    if attribute == "backend":

        return (
            f"J'ai enregistré que le backend "
            f"utilise {value}."
        )

    if attribute == "base_de_donnees":

        return (
            f"J'ai enregistré que le projet "
            f"utilise {value}."
        )

    if attribute == "frontend":

        return (
            f"J'ai enregistré que le frontend "
            f"utilise {value}."
        )

    if attribute == "type":

        return (
            f"J'ai enregistré que JARVIS "
            f"est un {value}."
        )

    return (
        f"J'ai enregistré : {attribute} = {value}."
    )  


def get_project_information():

    user = load_memory()

    structured = user.get(
        "structured_memory",
        {}
    )

    return structured.get(
        "projet",
        {}
    )