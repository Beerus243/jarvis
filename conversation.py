history = []


def add_message(role, message):

    history.append({
        "role": role,
        "message": message
    })


def get_history():

    return history


def get_last_user_message():

    for message in reversed(history):

        if message["role"] == "user":
            return message["message"]

    return None


def get_recent_history(limit=5):

    return history[-limit:]


def clear_history():

    history.clear()
