import json


MEMORY_FILE = "user.json"


# ============================================================
# CHARGER LA MÉMOIRE
# ============================================================

def load_memory():

    try:

        with open(MEMORY_FILE, "r") as f:
            return json.load(f)

    except FileNotFoundError:

        return {
            "identite": {},
            "preferences": {},
            "memory": {},
            "habits": {}
        }


# ============================================================
# SAUVEGARDER LA MÉMOIRE
# ============================================================

def save_memory(user):

    with open(MEMORY_FILE, "w") as f:

        json.dump(
            user,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# MÉMORISER UNE INFORMATION
# ============================================================

def remember(key, value):

    user = load_memory()

    if "memory" not in user:
        user["memory"] = {}

    user["memory"][key] = value

    save_memory(user)

    return True


# ============================================================
# RÉCUPÉRER UNE INFORMATION
# ============================================================

def recall(key):

    user = load_memory()

    return user.get("memory", {}).get(key)


# ============================================================
# ANALYSER UNE INFORMATION À MÉMORISER
# ============================================================

def analyze_memory(message):

    message = message.lower().strip()


    # --------------------------------------------------------
    # COULEUR PRÉFÉRÉE
    # --------------------------------------------------------

    if "ma couleur préférée est" in message:

        value = message.split(
            "ma couleur préférée est",
            1
        )[1].strip()

        if value:

            user = load_memory()

            if "preferences" not in user:
                user["preferences"] = {}

            user["preferences"]["couleur"] = value

            save_memory(user)

            return (
                f"J'ai retenu que votre couleur "
                f"préférée est {value}."
            )


    # --------------------------------------------------------
    # MUSIQUE PRÉFÉRÉE
    # --------------------------------------------------------

    if "ma musique préférée est" in message:

        value = message.split(
            "ma musique préférée est",
            1
        )[1].strip()

        if value:

            user = load_memory()

            if "preferences" not in user:
                user["preferences"] = {}

            user["preferences"]["musique"] = value

            save_memory(user)

            return (
                f"J'ai retenu que votre musique "
                f"préférée est {value}."
            )


    # --------------------------------------------------------
    # PROJET
    # --------------------------------------------------------

    if "je travaille sur" in message:

        value = message.split(
            "je travaille sur",
            1
        )[1].strip()

        if value:

            remember(
                "projet_actuel",
                value
            )

            return (
                f"Compris. Je retiens que vous "
                f"travaillez sur {value}."
            )


    # --------------------------------------------------------
    # NOM
    # --------------------------------------------------------

    if "je m'appelle" in message:

        value = message.split(
            "je m'appelle",
            1
        )[1].strip()

        if value:

            user = load_memory()

            if "identite" not in user:
                user["identite"] = {}

            user["identite"]["name"] = value

            save_memory(user)

            return (
                f"Très bien, je retiens que "
                f"vous vous appelez {value}."
            )


    return None


# ============================================================
# RECHERCHE DANS LA MÉMOIRE
# ============================================================

def recall_memory(message):

    message = message.lower().strip()

    user = load_memory()


    # --------------------------------------------------------
    # COULEUR
    # --------------------------------------------------------

    if "couleur" in message:

        value = user.get(
            "preferences",
            {}
        ).get("couleur")

        if value:

            return f"Votre couleur préférée est {value}."

        return "Je ne connais pas encore votre couleur préférée."


    # --------------------------------------------------------
    # MUSIQUE
    # --------------------------------------------------------

    if "musique" in message:

        value = user.get(
            "preferences",
            {}
        ).get("musique")

        if value:

            return f"Votre musique préférée est {value}."

        return "Je ne connais pas encore votre musique préférée."


    # --------------------------------------------------------
    # PROJET
    # --------------------------------------------------------

    if "projet" in message:

        value = user.get(
            "memory",
            {}
        ).get("projet_actuel")

        if value:

            return f"Vous travaillez actuellement sur {value}."

        return "Je ne connais pas encore votre projet actuel."


    # --------------------------------------------------------
    # NOM
    # --------------------------------------------------------

    if "nom" in message or "appelle" in message:

        value = user.get(
            "identite",
            {}
        ).get("name")

        if value:

            return f"Vous vous appelez {value}."

        return "Je ne connais pas encore votre nom."


    return None