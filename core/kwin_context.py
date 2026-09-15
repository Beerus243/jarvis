"""Contexte KWin en lecture seule : fournisseur externe ou script éphémère.

Le Python système utilise dbus-next pour un instantané de la fenêtre active.
Le script est immédiatement déchargé ; si ce transport manque, le contexte
est déclaré indisponible. Aucune commande XWayland n'est utilisée.
"""

import json
from pathlib import Path
import os
import shutil
import subprocess
import re


def _empty_window():
    return {
        "available": False,
        "id": None,
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
    if not provider:
        if os.getenv("XDG_SESSION_TYPE") == "wayland":
            snapshot = _read_snapshot()
            if snapshot is not None:
                return snapshot
        return _fetch_via_dbus()
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

def _read_snapshot():
    """Pas de dépendance supplémentaire dans le venv Kokoro."""
    try:
        result = subprocess.run(['/usr/bin/python3', str(Path(__file__).with_name('kwin_snapshot.py'))],
                                capture_output=True, text=True, timeout=10, check=False)
        if result.returncode != 0 or len(result.stdout) > 128 * 1024:
            return None
        payload = json.loads(result.stdout)
        return payload if isinstance(payload, dict) and isinstance(payload.get('windows'), list) else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _dbus_call(path, method):
    tool = shutil.which("qdbus") or shutil.which("qdbus6")
    if tool:
        command = [tool, "org.kde.KWin", path, method]
    elif shutil.which("dbus-send"):
        command = ["dbus-send", "--session", "--print-reply", "--dest=org.kde.KWin", path, method]
    else:
        return None
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=2)
        return result.stdout if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None

def _fetch_via_dbus():
    """Lecture opportuniste de l'API KWin; aucune action n'est envoyée."""
    listing = _dbus_call('/KWin', 'org.kde.KWin.windowList')
    active_raw = _dbus_call('/KWin', 'org.kde.KWin.activeWindow')
    if not listing or not active_raw:
        return None
    ids = [int(value) for value in re.findall(r'\b\d+\b', listing)]
    active_match = re.findall(r'\b\d+\b', active_raw)
    active_id = int(active_match[-1]) if active_match else None
    windows = []
    for window_id in ids:
        base = f'/Window_{window_id}'
        title_raw = _dbus_call(base, 'org.kde.KWin.Window.caption') or ''
        class_raw = _dbus_call(base, 'org.kde.KWin.Window.windowClass') or ''
        geometry_raw = _dbus_call(base, 'org.kde.KWin.Window.geometry') or ''
        def clean(value):
            match = re.search(r'"(.*)"', value)
            return match.group(1) if match else value.strip()
        windows.append({'id': window_id, 'title': clean(title_raw), 'application': clean(class_raw), 'pid': None, 'active': window_id == active_id, 'closeable': False, 'geometry': clean(geometry_raw)})
    return {'windows': windows, 'active_window_id': active_id}


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
