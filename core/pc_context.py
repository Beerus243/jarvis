"""Contexte dynamique du PC, collecté localement et sans mémoire persistante."""

import getpass
import os
import platform
import shutil
import socket
from pathlib import Path


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
        "applications": [],
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
