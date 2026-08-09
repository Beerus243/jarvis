history = []


def add_message(role, message):

    history.append({
        "role": role,
        "message": message
    })


def get_history():

    return history


def get_last_message():

    if history:
        return history[-1]["message"]

    return None


def clear_history():

    history.clear()