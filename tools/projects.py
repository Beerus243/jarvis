"""Gestion du registre des projets de JARVIS."""

import json
from pathlib import Path


PROJECTS_FILE = (
    Path(__file__).resolve().parent.parent
    / "memory"
    / "projects.json"
)


def load_projects():
    """Charge le registre des projets."""

    try:
        with PROJECTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {}

        return data

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
    ):
        return {}


def save_projects(projects):
    """Sauvegarde le registre des projets."""

    PROJECTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with PROJECTS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            projects,
            file,
            ensure_ascii=False,
            indent=4,
        )


def resolve_project(project):
    """
    Résout un nom de projet vers son chemin.

    Exemple :
        jarvis -> ~/dev/jarvis
    """

    key = str(project or "").casefold().strip()

    if not key:
        return None

    projects = load_projects()

    entry = projects.get(key)

    if not isinstance(entry, dict):
        return None

    path = entry.get("path")

    if not path:
        return None

    return {
        "key": key,
        "name": entry.get("name", key),
        "path": path,
    }


def list_projects():
    """Retourne les projets enregistrés."""

    projects = load_projects()

    result = []

    for key, entry in projects.items():

        if not isinstance(entry, dict):
            continue

        path = entry.get("path")

        if not path:
            continue

        result.append({
            "key": key,
            "name": entry.get("name", key),
            "path": path,
        })

    return result


def register_project(name, path):
    """
    Ajoute ou met à jour un projet.

    Exemple :
        register_project("RDV", "~/dev/rdv")
    """

    name = str(name or "").strip()
    path = str(path or "").strip()

    if not name or not path:
        return False, "Nom ou chemin manquant."

    key = name.casefold()

    projects = load_projects()

    projects[key] = {
        "name": name,
        "path": path,
    }

    save_projects(projects)

    return True, f"Projet {name} enregistré."


def format_projects():
    """Produit une réponse naturelle pour la liste des projets."""

    projects = list_projects()

    if not projects:
        return "Je n'ai aucun projet enregistré."

    if len(projects) == 1:
        project = projects[0]

        return (
            f"J'ai un projet enregistré : "
            f"{project['name']}."
        )

    names = [
        project["name"]
        for project in projects
    ]

    return (
        f"J'ai {len(names)} projets enregistrés : "
        + ", ".join(names)
        + "."
    )
