from .models import PCAction, ActionResult
from .screenshot import ScreenCapture
from pathlib import Path
import shutil
import subprocess
from tools.applications import open_application, close_application
from tools.browser import open_url

ALLOWED_ACTIONS = {
    "SCREENSHOT", "OPEN_APPLICATION", "CLOSE_APPLICATION", "OPEN_URL",
    "OPEN_FOLDER", "FILE_OPEN", "FILE_CREATE", "FILE_COPY", "FILE_MOVE", "FILE_DELETE",
    "VOLUME_UP", "VOLUME_DOWN", "VOLUME_MUTE", "MEDIA_PLAY", "MEDIA_PAUSE",
    "MEDIA_NEXT", "MEDIA_PREVIOUS",
}

def _safe_path(value):
    path = Path(str(value or "")).expanduser().resolve()
    home = Path.home().resolve()
    if path != home and home not in path.parents:
        return None
    return path

def _file_action(action):
    p = action.parameters or {}
    source = _safe_path(p.get("source") or p.get("path"))
    target = _safe_path(p.get("target"))
    kind = action.action_type
    if kind == "OPEN_FOLDER":
        folder = _safe_path(p.get("path"))
        if folder and not str(p.get("path", "")).startswith(("/", "~")):
            folder = (Path.home() / str(p.get("path"))).resolve()
        if not folder or not folder.is_dir(): return ActionResult(kind, False, "Dossier introuvable.", error="NOT_FOUND")
        try: subprocess.Popen(["xdg-open", str(folder)])
        except OSError as exc: return ActionResult(kind, False, "Impossible d'ouvrir le dossier.", error=str(exc))
        return ActionResult(kind, True, f"J'ouvre le dossier {folder.name}.")
    if kind == "FILE_OPEN":
        if not source or not source.exists(): return ActionResult(kind, False, "Fichier introuvable.", error="NOT_FOUND")
        try: subprocess.Popen(["xdg-open", str(source)])
        except OSError as exc: return ActionResult(kind, False, "Impossible d'ouvrir le fichier.", error=str(exc))
        return ActionResult(kind, True, f"J'ouvre {source.name}.")
    if not source or (kind != "FILE_CREATE" and not source.exists()):
        return ActionResult(kind, False, "Chemin invalide ou fichier introuvable.", error="INVALID_PATH")
    try:
        if kind == "FILE_CREATE":
            if not source: return ActionResult(kind, False, "Chemin invalide.", error="INVALID_PATH")
            source.parent.mkdir(parents=True, exist_ok=True); source.touch(exist_ok=False)
            return ActionResult(kind, True, f"Fichier créé : {source.name}.")
        if not target: return ActionResult(kind, False, "Destination invalide.", error="INVALID_PATH")
        if kind == "FILE_COPY": shutil.copy2(source, target)
        elif kind == "FILE_MOVE": shutil.move(str(source), str(target))
        elif kind == "FILE_DELETE": source.unlink()
        return ActionResult(kind, True, "Opération sur le fichier effectuée.")
    except (OSError, shutil.Error) as exc:
        return ActionResult(kind, False, "Opération sur le fichier échouée.", error=str(exc))

def _system_action(action):
    commands = {
        "VOLUME_UP": ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%+"],
        "VOLUME_DOWN": ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"],
        "VOLUME_MUTE": ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"],
        "MEDIA_PLAY": ["playerctl", "play"], "MEDIA_PAUSE": ["playerctl", "pause"],
        "MEDIA_NEXT": ["playerctl", "next"], "MEDIA_PREVIOUS": ["playerctl", "previous"],
    }
    command = commands[action.action_type]
    if not shutil.which(command[0]): return ActionResult(action.action_type, False, "Contrôle non disponible.", error="NOT_SUPPORTED")
    try:
        result = subprocess.run(command, check=False, capture_output=True, timeout=5)
        if result.returncode == 0: return ActionResult(action.action_type, True, "Commande audio exécutée.")
        return ActionResult(action.action_type, False, "La commande audio a échoué.", error="COMMAND_FAILED")
    except (OSError, subprocess.SubprocessError) as exc:
        return ActionResult(action.action_type, False, "La commande audio a échoué.", error=str(exc))

def execute_pc_action(action: PCAction, *, capture=None):
    if not isinstance(action, PCAction) or action.action_type not in ALLOWED_ACTIONS:
        return ActionResult(getattr(action, "action_type", "UNKNOWN_ACTION"), False, "Action PC bloquée.", error="UNKNOWN_ACTION")
    if action.action_type == "SCREENSHOT": return (capture or ScreenCapture()).capture()
    if action.action_type == "OPEN_APPLICATION":
        target = (action.parameters or {}).get("application") or (action.parameters or {}).get("target", "")
        ok, message = open_application(target)
        return ActionResult(action.action_type, bool(ok), message, error=None if ok else "FAILED")
    if action.action_type == "CLOSE_APPLICATION":
        target = (action.parameters or {}).get("application") or (action.parameters or {}).get("target", "")
        ok, message = close_application(target)
        return ActionResult(action.action_type, bool(ok), message, error=None if ok else "FAILED")
    if action.action_type == "OPEN_URL":
        url = (action.parameters or {}).get("url", "")
        ok, message = open_url(url)
        return ActionResult(action.action_type, bool(ok), message, error=None if ok else "FAILED")
    if action.action_type.startswith("FILE_"): return _file_action(action)
    if action.action_type.startswith("VOLUME_") or action.action_type.startswith("MEDIA_"): return _system_action(action)
    return ActionResult(action.action_type, False, "Action non supportée.", error="NOT_SUPPORTED")
