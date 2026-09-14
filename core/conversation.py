import json
from config.settings import CONVERSATION_FILE
from core.json_store import atomic_write

history = []

def _write_conversation(conversation):
    atomic_write(CONVERSATION_FILE, conversation)


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
    del history[:-100]

    from core.json_store import update
    def append(conversation):
        return (conversation + [{"role": role, "message": message}])[-100:]
    update(CONVERSATION_FILE, append, default=[])


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
    history.clear()
    atomic_write(CONVERSATION_FILE, [])
