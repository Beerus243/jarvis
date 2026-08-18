import json

from memory.text_normalizer import normalize_text
from memory.project_parser import parse_project_information
from memory.project_questions import detect_project_question
from memory.project_responses import format_project_update
from config.settings import MEMORY_FILE

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


def update_project_attribute(attribute, value):

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



def update_project_information(attribute, value):

    old_value = get_project_attribute(attribute)

    update_project(
        attribute,
        value
    )

    if old_value is None:

        return (
            f"J'ai enregistré que le {attribute} "
            f"est {value}."
        )

    if old_value == value:

        return (
            f"Cette information est déjà enregistrée : "
            f"{value}."
        )

    return (
        f"J'ai mis à jour le {attribute} : "
        f"{old_value} → {value}."
    )


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

    question_type = detect_project_question(message)

    # ========================================================
    # LANGAGE
    # ========================================================

    if question_type == "langage":

        langage = project.get("langage")

        if langage:

            return (
                f"Le projet est développé en {langage}."
            )

    # ========================================================
    # BACKEND
    # ========================================================

    if question_type == "backend":

        backend = project.get("backend")

        if backend:

            return (
                f"Le backend du projet utilise {backend}."
            )

    # ========================================================
    # FRONTEND
    # ========================================================

    if question_type == "frontend":

        frontend = project.get("frontend")

        if frontend:

            return (
                f"Le frontend du projet utilise {frontend}."
            )

    # ========================================================
    # BASE DE DONNÉES
    # ========================================================

    if question_type == "base_de_donnees":

        database = project.get("base_de_donnees")

        if database:

            return (
                f"Le projet utilise "
                f"{database} comme base de données."
            )
            # ========================================================
    # TYPE DU PROJET
    # ========================================================

    if (
        "type du projet" in text
        or "type de projet" in text
        or "quel type de projet" in text
    ):

        project_type = project.get("type")

        if project_type:

            return (
                f"JARVIS est un {project_type}."
            )

    # ========================================================
    # STACK
    # ========================================================

    if question_type == "stack":

        langage = project.get("langage")
        backend = project.get("backend")
        frontend = project.get("frontend")
        database = project.get("base_de_donnees")

        elements = []

        if langage:
            elements.append(
                f"développé en {langage}"
            )

        if backend:
            elements.append(
                f"avec {backend} en backend"
            )

        if frontend:
            elements.append(
                f"{frontend} en frontend"
            )

        if database:
            elements.append(
                f"{database} comme base de données"
            )

        if elements:

            return (
                "La stack actuelle de JARVIS est : "
                + ", ".join(elements)
                + "."
            )
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


def analyze_project_information_v2(message):

    result = parse_project_information(
        message
    )

    if not result:
        return None

    attribute = result["attribute"]
    value = result["value"]

    return update_project_information(
        attribute,
        value
    )

def analyze_project_update(message):

    information = parse_project_information(message)

    if not information:
        return None

    attribute = information["attribute"]
    new_value = information["value"]

    old_value = get_project_attribute(attribute)

    # ========================================================
    # AUCUNE ANCIENNE VALEUR
    # ========================================================

    if old_value is None:

        update_project_attribute(
            attribute,
            new_value
        )

        return format_project_update(
            attribute,
            None,
            new_value
        )

    # ========================================================
    # MÊME VALEUR
    # ========================================================

    if old_value == new_value:

        return format_project_update(
            attribute,
            old_value,
            new_value
        )

    # ========================================================
    # NOUVELLE VALEUR
    # ========================================================

    update_project_attribute(
        attribute,
        new_value
    )

    return format_project_update(
        attribute,
        old_value,
        new_value
    )
