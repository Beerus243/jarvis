"""Safe user-level PATH repair helpers (no sudo, no global files)."""
from __future__ import annotations
import os
from pathlib import Path

def validate_user_path(path: str | Path) -> Path:
    candidate=Path(path).expanduser().resolve()
    home=Path.home().resolve()
    if candidate != home and home not in candidate.parents:
        raise ValueError('Le chemin doit rester dans le répertoire utilisateur.')
    if not candidate.is_dir(): raise ValueError('Le répertoire à ajouter n’existe pas.')
    return candidate

def prepare_path_update(directory: str | Path, variable: str='PATH') -> dict:
    path=validate_user_path(directory)
    if variable not in {'PATH','JAVA_HOME','ANDROID_SDK_ROOT'}: raise ValueError('Variable non autorisée.')
    return {'variable':variable,'directory':str(path),'export':f'export {variable}="{path}:${variable}"','requires_confirmation':True}

def apply_user_path_update(update: dict, *, confirmed: bool=False, profile: str | Path | None=None) -> bool:
    if not confirmed: return False
    target=Path(profile or (Path.home()/'.profile')).expanduser().resolve()
    home=Path.home().resolve()
    if target != home and home not in target.parents: raise ValueError('Profil utilisateur invalide.')
    line=update.get('export')
    if not line or update.get('variable') not in {'PATH','JAVA_HOME','ANDROID_SDK_ROOT'}: raise ValueError('Mise à jour invalide.')
    existing=target.read_text(encoding='utf-8') if target.exists() else ''
    if line not in existing:
        target.write_text(existing + ('\n' if existing and not existing.endswith('\n') else '') + line + '\n',encoding='utf-8')
    return True
