"""Lecture du contexte des fenêtres KWin sous Wayland.

KWin expose les fenêtres via son KWin Scripting API (workspace.activeWindow
et workspace.stackingOrder). Le script KWin qui publie ces données n'est pas
installé par JARVIS : en son absence, ce module signale explicitement que le
contexte est indisponible au lieu d'utiliser wmctrl ou XWayland.
"""

import json
import os
import shutil
import subprocess


def _empty_window():
    return {
        "available": False,
        "application": None,
        "title": None,
        "pid": None,
        "active": False,
        "closeable": False,
    }


def _unavailable():
    return {"active_window": _empty_window(), "windows": []}


def _read_provider():
    """Lit un fournisseur KWin script optionnel, sans commande arbitraire."""
    provider = shutil.which("jarvis-kwin-context")
    if not provider or os.environ.get("XDG_SESSION_TYPE") != "wayland":
        return None
    try:
        result = subprocess.run(
            [provider], capture_output=True, text=True, check=False, timeout=2
        )
        if result.returncode != 0:
            return None
        payload = json.loads(result.stdout)
        return payload if isinstance(payload, dict) else None
    except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError):
        return None


def get_kwin_context(provider=None):
    payload = provider if provider is not None else _read_provider()
    if not isinstance(payload, dict):
        return _unavailable()
    windows = payload.get("windows")
    if not isinstance(windows, list):
        return _unavailable()
    normalized = []
    for window in windows:
        if not isinstance(window, dict):
            continue
        item = _empty_window()
        item.update({key: window.get(key) for key in item if key in window})
        item["available"] = bool(window.get("available", True))
        item["active"] = bool(window.get("active", False))
        item["closeable"] = bool(window.get("closeable", False))
        normalized.append(item)
    active = next((item for item in normalized if item["active"]), _empty_window())
    return {"active_window": active, "windows": normalized}


def list_windows(provider=None):
    return get_kwin_context(provider).get("windows", [])


def get_active_window(provider=None):
    return get_kwin_context(provider).get("active_window", _empty_window())


def get_window_by_pid(pid, provider=None):
    try:
        target = int(pid)
    except (TypeError, ValueError):
        return None
    return next((item for item in list_windows(provider) if item.get("pid") == target), None)


def can_close_window(window):
    return bool(isinstance(window, dict) and window.get("available") and window.get("closeable"))
