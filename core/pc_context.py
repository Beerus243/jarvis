"""Contexte dynamique du PC, collecté localement et sans mémoire persistante."""

import getpass
import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path
from core.kwin_context import get_kwin_context


KNOWN_APPLICATIONS = {
    "vscode": {
        "name": "VS Code",
        "process_names": {"code"},
        "capabilities": ["open"],
        "controllable": False,
    },
    "chrome": {
        "name": "Chrome",
        "process_names": {"chrome", "google-chrome", "google-chrome-stable"},
        "capabilities": ["open"],
        "controllable": False,
    },
    "firefox": {
        "name": "Firefox",
        "process_names": {"firefox"},
        "capabilities": ["open"],
        "controllable": False,
    },
    "spotify": {
        "name": "Spotify",
        "process_names": {"spotify"},
        "capabilities": ["open", "spotify_control"],
        "controllable": True,
    },
    "dolphin": {
        "name": "Dolphin",
        "process_names": {"dolphin"},
        "capabilities": ["open"],
        "controllable": False,
    },
    "terminal": {
        "name": "Terminal",
        "process_names": {"konsole", "ptyxis", "gnome-terminal", "alacritty", "kitty", "foot"},
        "capabilities": ["open"],
        "controllable": False,
    },
}


def _process_snapshot():
    """Retourne les processus visibles, sans envoyer de signal au système."""
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid=,ppid=,comm="],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []

    processes = []
    for line in result.stdout.splitlines():
        fields = line.split(None, 2)
        if len(fields) != 3:
            continue
        try:
            processes.append({"pid": int(fields[0]), "ppid": int(fields[1]), "comm": fields[2].strip()})
        except ValueError:
            continue
    return processes


def get_known_applications(processes=None):
    """Détecte uniquement les applications de la liste blanche du projet."""
    processes = _process_snapshot() if processes is None else processes
    applications = []
    for key, definition in KNOWN_APPLICATIONS.items():
        matches = [item for item in processes if item["comm"] in definition["process_names"]]
        match_pids = {item["pid"] for item in matches}
        # Le PID racine est celui qui n'est pas enfant d'un autre processus
        # correspondant. À défaut, on garde le plus ancien PID observé.
        roots = [item for item in matches if item["ppid"] not in match_pids]
        primary = min(roots or matches, key=lambda item: item["pid"]) if matches else None
        applications.append({
            "name": definition["name"],
            "running": bool(matches),
            "pid": primary["pid"] if primary else None,
            "controllable": bool(definition["controllable"] and matches),
            "capabilities": list(definition["capabilities"]),
        })
    return applications


def _battery():
    try:
        batteries = list(Path("/sys/class/power_supply").glob("BAT*/capacity"))
        status = list(Path("/sys/class/power_supply").glob("BAT*/status"))
        level = int(batteries[0].read_text().strip()) if batteries else None
        power = status[0].read_text().strip().lower() if status else "unknown"
        return {"level": level, "charging": power in {"charging", "full"}, "status": power}
    except (OSError, ValueError):
        return {"level": None, "charging": None, "status": "unknown"}


def _audio():
    return {"server": bool(shutil.which("pactl")), "default_sink": os.environ.get("PULSE_SINK")}


def get_pc_context():
    kwin = get_kwin_context()
    return {
        "os": platform.platform(),
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "home": str(Path.home()),
        "current_directory": os.getcwd(),
        "battery": _battery(),
        "power": _battery().get("status", "unknown"),
        "network": {"available": bool(socket.gethostname())},
        "audio": _audio(),
        "applications": get_known_applications(),
        "active_window": kwin["active_window"],
        "windows": kwin["windows"],
    }


def answer_pc_question(message, context=None):
    text = str(message or "").casefold()
    context = context or get_pc_context()
    if "système" in text or "systeme" in text:
        return f"Tu utilises {context['os']}."
    if "quel pc" in text or "sur quel" in text:
        return f"Tu es sur le PC {context['hostname']}."
    if "batterie" in text or "charge" in text:
        battery = context["battery"]
        if battery.get("level") is None:
            return "Je ne peux pas lire le niveau de batterie localement."
        return f"La batterie est à {battery['level']}%."
    if "état audio" in text or "etat audio" in text:
        return "Le contexte audio local est disponible." if context["audio"]["server"] else "Aucun serveur audio local détecté."
    return None
