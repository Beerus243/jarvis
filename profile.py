from memory import remember


def analyze_profile(message):

    message = message.lower()


    if "j'aime" in message:

        valeur = message.split("j'aime")[1].strip()

        remember(
            "aime",
            valeur
        )

        return f"Je retiens que vous aimez {valeur}."


    elif "je préfère" in message:

        valeur = message.split("je préfère")[1].strip()

        remember(
            "prefere",
            valeur
        )

        return f"Je retiens votre préférence pour {valeur}."


    return None