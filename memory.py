import json
from datetime import datetime


def save_history(user_message, jarvis_response):

    conversation = {
        "date": str(datetime.now()),
        "user": user_message,
        "jarvis": jarvis_response
    }

    try:
        with open("history.json", "r") as f:
            history = json.load(f)

    except:
        history = []


    history.append(conversation)
    history = history[-100:]


    with open("history.json", "w") as f:
        json.dump(history, f, indent=4)


def remember(key, value):

    with open("user.json", "r") as f:
        user = json.load(f)

    user["memory"][key] = value

    with open("user.json", "w") as f:
        json.dump(user, f, indent=4)