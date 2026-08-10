from conversation import get_recent_history
import json


CONVERSATION_FILE = "conversation.json"


def get_recent_history(limit=5):

    try:

        with open(CONVERSATION_FILE, "r") as f:
            history = json.load(f)

        return history[-limit:]

    except FileNotFoundError:

        return []

    except json.JSONDecodeError:

        return []

        return []

    except json.JSONDecodeError:

        return []

def get_context():

    history = get_recent_history(5)

    if not history:
        return []

    context = []

    for message in history:

        context.append({
            "role": message["role"],
            "content": message["message"]
        })

    return context