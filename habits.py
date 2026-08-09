import json


def add_habit(habit):

    with open("user.json", "r") as f:
        user = json.load(f)


    if habit in user["habits"]:
        user["habits"][habit] += 1

    else:
        user["habits"][habit] = 1


    with open("user.json", "w") as f:
        json.dump(user, f, indent=4)


def get_habits():

    with open("user.json", "r") as f:
        user = json.load(f)

    return user["habits"]

def analyze_habit(message):

    message = message.lower()


    if "salle" in message or "sport" in message:
        add_habit("sport")
        return "J'ai noté votre activité sportive."


    if "coder" in message or "programmer" in message:
        add_habit("programmation")
        return "J'ai noté votre activité de programmation."


    return None

    