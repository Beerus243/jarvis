import json
from config.settings import CONVERSATION_FILE
from core.conversation import get_recent_history

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
