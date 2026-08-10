from conversation import get_recent_history


def get_context():

    history = get_recent_history(5)

    if not history:
        return ""

    context = []

    for message in history:

        role = message["role"]
        text = message["message"]

        context.append(f"{role}: {text}")

    return "\n".join(context)
