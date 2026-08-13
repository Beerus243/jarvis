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

    # ========================================================
    # LANGAGE
    # ========================================================

    if (
        "langage" in text
        or "language" in text
        or "langage de programmation" in text
    ):

        langage = project.get("langage")

        if langage:

            return (
                f"Le projet est développé en {langage}."
            )

    # ========================================================
    # BACKEND
    # ========================================================

    if "backend" in text:

        backend = project.get("backend")

        if backend:

            return (
                f"Le backend du projet utilise {backend}."
            )

    # ========================================================
    # FRONTEND
    # ========================================================

    if "frontend" in text:

        frontend = project.get("frontend")

        if frontend:

            return (
                f"Le frontend du projet utilise {frontend}."
            )

    # ========================================================
    # BASE DE DONNÉES
    # ========================================================

    if (
        "base de données" in text
        or "base de donnée" in text
        or "base de donnees" in text
        or "base de donnee" in text
        or "database" in text
        or "bdd" in text
    ):

        database = project.get("base_de_donnees")

        if database:

            return (
                f"Le projet utilise "
                f"{database} comme base de données."
            )

    # ========================================================
    # STACK
    # ========================================================

    if "stack" in text:

        langage = project.get("langage")
        backend = project.get("backend")
        frontend = project.get("frontend")
        database = project.get("base_de_donnees")

        if any([
            langage,
            backend,
            frontend,
            database
        ]):

            return (
                "La stack actuelle de JARVIS est : "
                f"développé en {langage}, "
                f"avec {backend} en backend, "
                f"{frontend} en frontend, "
                f"et {database} comme base de données."
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

    # --------------------------------------------------------
    # Aucune ancienne valeur
    # --------------------------------------------------------

    if old_value is None:

        update_project_attribute(
            attribute,
            new_value
        )

        return (
            f"J'ai enregistré que "
            f"{attribute} utilise {new_value}."
        )

    # --------------------------------------------------------
    # Même valeur
    # --------------------------------------------------------

    if old_value == new_value:

        return (
            f"Cette information est déjà enregistrée : "
            f"{new_value}."
        )

    # --------------------------------------------------------
    # Nouvelle valeur
    # --------------------------------------------------------

    update_project_attribute(
        attribute,
        new_value
    )

    return (
        f"J'ai mis à jour {attribute} : "
        f"{old_value} → {new_value}."
    )