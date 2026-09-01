import json
import threading
import logging
from threading import Thread
from config.settings import CONVERSATION_FILE

history = []
_write_lock = threading.Lock()

def _write_conversation(conversation):
    try:
        with _write_lock:
            with open(CONVERSATION_FILE, "w") as f:
                json.dump(conversation, f, indent=4, ensure_ascii=False)
    except OSError as exc:
        logging.debug("Écriture conversation échouée: %s", exc)


def get_history():

    return history


def get_last_user_message():

    for message in reversed(history):

        if message["role"] == "user":
            return message["message"]

    return None


def get_recent_history(limit=5):
    if history:
        return history[-limit:]
    return load_conversation()[-limit:]


def clear_history():

    history.clear()



# ============================================================
# CHARGER LA CONVERSATION
# ============================================================

def load_conversation():

    try:

        with open(CONVERSATION_FILE, "r") as f:
            return json.load(f)

    except FileNotFoundError:

        return []


# ============================================================
# AJOUTER UN MESSAGE
# ============================================================

def add_message(role, message):

    history.append({
        "role": role,
        "message": message
    })

    conversation = load_conversation()

    conversation.append({
        "role": role,
        "message": message
    })

    # Garder uniquement les 10 derniers messages
    conversation = conversation[-10:]

    Thread(target=_write_conversation, args=(conversation,), daemon=True).start()


def get_last_message():
    recent = get_recent_history(1)
    return recent[-1] if recent else None


# ============================================================
# RÉCUPÉRER LE CONTEXTE
# ============================================================

def get_context():

    conversation = load_conversation()

    return conversation


# ============================================================
# EFFACER LE CONTEXTE
# ============================================================

def clear_conversation():

    with open(CONVERSATION_FILE, "w") as f:

        json.dump([], f)
