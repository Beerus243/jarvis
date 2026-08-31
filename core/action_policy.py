"""Politique locale de sécurité des actions JARVIS."""

SAFE_ACTION = "SAFE_ACTION"
CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
BLOCKED_ACTION = "BLOCKED_ACTION"

_POLICY = {
    "GREETINGS": SAFE_ACTION,
    "GET_TIME": SAFE_ACTION,
    "OPEN_BROWSER": SAFE_ACTION,
    "OPEN_SPOTIFY": SAFE_ACTION,
    "PLAY_MUSIC": SAFE_ACTION,
    "OPEN_TERMINAL": SAFE_ACTION,
    "OPEN_VSCODE": SAFE_ACTION,
    "OPEN_PROJECT": SAFE_ACTION,
    "LIST_PROJECTS": SAFE_ACTION,
    "OPEN_FIREFOX": SAFE_ACTION,
    "OPEN_SITE": SAFE_ACTION,
    "OPEN_WEBSITE": SAFE_ACTION,
    "OPEN_FOLDER": SAFE_ACTION,
    "OPEN_APPLICATION": SAFE_ACTION,
    "SEARCH_MUSIC": SAFE_ACTION,
    "OPEN_URL": SAFE_ACTION,
    "SEARCH_WEB": SAFE_ACTION,
    "SEARCH_WIKIPEDIA": SAFE_ACTION,
    "PAUSE_MUSIC": SAFE_ACTION,
    "RESUME_MUSIC": SAFE_ACTION,
    "NEXT_TRACK": SAFE_ACTION,
    "PREVIOUS_TRACK": SAFE_ACTION,
    "SCREENSHOT": SAFE_ACTION,
    "CLOSE_APPLICATION": CONFIRMATION_REQUIRED,
    "RUN_COMMAND": CONFIRMATION_REQUIRED,
    "DELETE_FILE": BLOCKED_ACTION,
    "FORMAT_DISK": BLOCKED_ACTION,
    "ROOT_COMMAND": BLOCKED_ACTION,
}


def classify_action(action):
    return _POLICY.get(action, BLOCKED_ACTION)


def detect_sensitive_request(message):
    text = str(message or "").casefold()
    if any(word in text for word in ("supprime", "efface", "formatte")):
        return "DELETE_FILE"
    if any(word in text for word in ("ferme l application", "fermer l application", "ferme cette application")):
        return "CLOSE_APPLICATION"
    return None
