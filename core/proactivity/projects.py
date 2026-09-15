"""Rapprochement avec le registre explicite ; titres transitoires, sans scan disque."""
from pathlib import Path
import re
from core.command_understanding import normalize_command
from tools.projects import load_projects

DEV_APPS = {'code', 'code-oss', 'codium', 'konsole', 'terminal', 'pycharm', 'jetbrains-pycharm', 'kate'}


def registered():
    result = []
    for key, entry in load_projects().items():
        if not isinstance(entry, dict) or not isinstance(entry.get('path'), str):
            continue
        path = Path(entry['path']).expanduser().resolve()
        if not path.is_relative_to(Path.home().resolve()) and not path.is_relative_to(Path.cwd().resolve()):
            continue
        result.append({'key': key, 'name': str(entry.get('name', key)), 'path': str(path)})
    return result


def find_project(name):
    matches = [p for p in registered() if normalize_command(name) in {normalize_command(p['key']), normalize_command(p['name'])}]
    return matches[0] if len(matches) == 1 else None


def identify(pc, declared=None):
    window = pc.get('active_window') or {}
    if not window.get('available'):
        return None
    app = str(window.get('application', '')).lower().rsplit('.', 1)[-1]
    if app not in DEV_APPS:
        return None
    title = normalize_command(window.get('title', ''))
    candidates = []
    for project in registered():
        aliases = {normalize_command(project['key']), normalize_command(project['name']), normalize_command(Path(project['path']).name)}
        if any(alias and re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', title) for alias in aliases):
            candidates.append(project)
    if len(candidates) == 1:
        return {**candidates[0], 'source': 'titre de la fenêtre active', 'confidence': 'observed'}
    if not candidates and declared:
        project = find_project(declared)
        if project:
            return {**project, 'source': 'projet déclaré par Fabrice, outil de développement actif', 'confidence': 'declared'}
    return None  # Plusieurs projets visibles ne permettent pas de trancher.
