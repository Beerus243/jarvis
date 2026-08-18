import json
from config.settings import HISTORY_FILE


def load_history():

    try:

        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except (FileNotFoundError, json.JSONDecodeError):

        return []


def save_message(user_message, jarvis_response):

    history = load_history()

    history.append({
        "user": user_message,
        "jarvis": jarvis_response
    })

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

def get_recent_history(limit=10):

    history = load_history()

    return history[-limit:]
