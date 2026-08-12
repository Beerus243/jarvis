import json
from datetime import datetime

MEMORY_FILE = "user.json"


# ============================================================
# CHARGER LA MÉMOIRE
# ============================================================

def load_memory():

    try:

        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except (FileNotFoundError, json.JSONDecodeError):

        return {}


# ============================================================
# SAUVEGARDER LA MÉMOIRE
# ============================================================

def save_memory(user):

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:

        json.dump(
            user,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# GÉNÉRER UN ID DE SOUVENIR
# ============================================================

def generate_memory_id(user):

    souvenirs = user.get("souvenirs", [])

    if not souvenirs:
        return "s001"

    numbers = []

    for souvenir in souvenirs:

        identifiant = souvenir.get("id", "")

        if identifiant.startswith("s"):

            try:
                numbers.append(
                    int(identifiant[1:])
                )

            except ValueError:
                pass

    if not numbers:
        return "s001"

    return f"s{max(numbers) + 1:03d}"


# ============================================================
# MÉMORISER UNE INFORMATION
# ============================================================

def remember(contenu, categorie, importance="moyenne"):

    user = load_memory()

    if "souvenirs" not in user:
        user["souvenirs"] = []

    souvenir = {

        "id": generate_memory_id(user),

        "contenu": contenu,

        "categorie": categorie,

        "date": datetime.now().isoformat(
            timespec="seconds"
        ),

        "importance": importance
    }

    user["souvenirs"].append(souvenir)

    save_memory(user)

    return souvenir


# ============================================================
# ANALYSER UNE INFORMATION À MÉMORISER
# ============================================================

def analyze_memory(message):

    original_message = message.strip()

    message = original_message.lower()


    # --------------------------------------------------------
    # COULEUR PRÉFÉRÉE
    # --------------------------------------------------------

    if "ma couleur préférée est" in message:

        value = original_message.split(
            "est",
            1
        )[1].strip()

        if value:

            remember(
                f"La couleur préférée de Fabrice est {value}",
                "preference",
                "moyenne"
            )

            return (
                f"J'ai retenu que votre couleur "
                f"préférée est {value}."
            )


    # --------------------------------------------------------
    # MUSIQUE PRÉFÉRÉE
    # --------------------------------------------------------

    if "ma musique préférée est" in message:

        value = original_message.split(
            "est",
            1
        )[1].strip()

        if value:

            remember(
                f"La musique préférée de Fabrice est {value}",
                "preference",
                "moyenne"
            )

            return (
                f"J'ai retenu que votre musique "
                f"préférée est {value}."
            )


    # --------------------------------------------------------
    # PROJET
    # --------------------------------------------------------

    if "je travaille sur" in message:

        value = original_message.split(
            "sur",
            1
        )[1].strip()

        if value:

            remember(
                f"Fabrice travaille sur {value}",
                "projet",
                "haute"
            )

            return (
                f"Compris. Je retiens que vous "
                f"travaillez sur {value}."
            )


    # --------------------------------------------------------
    # NOM
    # --------------------------------------------------------

    if "je m'appelle" in message:

        value = original_message.split(
            "je m'appelle",
            1
        )[1].strip()

        if value:

            remember(
                f"Fabrice s'appelle {value}",
                "identite",
                "haute"
            )

            return (
                f"Très bien, je retiens que "
                f"vous vous appelez {value}."
            )


    # --------------------------------------------------------
    # OBJECTIF
    # --------------------------------------------------------

    if "mon objectif est" in message:

        value = original_message.split(
            "mon objectif est",
            1
        )[1].strip()

        if value:

            remember(
                f"L'objectif de Fabrice est {value}",
                "objectif",
                "haute"
            )

            return (
                f"Je retiens votre objectif : {value}."
            )


    # --------------------------------------------------------
    # APPRENTISSAGE
    # --------------------------------------------------------

    if "j'apprends" in message:

        value = original_message.split(
            "j'apprends",
            1
        )[1].strip()

        if value:

            remember(
                f"Fabrice apprend {value}",
                "competence",
                "haute"
            )

            return (
                f"Je retiens que vous apprenez {value}."
            )


    return None


# ============================================================
# RECHERCHE DANS LA MÉMOIRE
# ============================================================
def recall_memory(message):

    message = message.lower().strip()

    user = load_memory()

    souvenirs = user.get("souvenirs", [])


    # ========================================================
    # PROJET
    # ========================================================

    mots_projet = [
        "projet",
        "travaille",
        "travail",
        "développe",
        "développer",
        "projet actuel"
    ]

    if any(mot in message for mot in mots_projet):

        resultats = [
            souvenir
            for souvenir in souvenirs
            if souvenir.get("categorie") == "projet"
        ]

        if resultats:

            souvenir = resultats[-1]

            contenu = souvenir["contenu"]

            return (
                f"D'après ma mémoire, {contenu}."
            )


        return "Je ne connais pas encore votre projet."


    # ========================================================
    # OBJECTIF
    # ========================================================

    mots_objectif = [
        "objectif",
        "but",
        "veux devenir",
        "veux faire"
    ]

    if any(mot in message for mot in mots_objectif):

        resultats = [
            souvenir
            for souvenir in souvenirs
            if souvenir.get("categorie") == "objectif"
        ]

        if resultats:

            souvenir = resultats[-1]

            return (
                f"D'après ma mémoire, "
                f"{souvenir['contenu']}."
            )


        return "Je ne connais pas encore votre objectif."


    # ========================================================
    # APPRENTISSAGE
    # ========================================================

    mots_competence = [
        "apprends",
        "apprentissage",
        "j'étudie",
        "j'étudie",
        "compétence",
        "apprendre"
    ]

    if any(
        mot in message
        for mot in mots_competence
    ):

        resultats = [
            souvenir
            for souvenir in souvenirs
            if souvenir.get("categorie") == "competence"
        ]

        if resultats:

            textes = [
                souvenir["contenu"]
                for souvenir in resultats
            ]

            return (
                "D'après ma mémoire, vous apprenez : "
                + ", ".join(textes)
                + "."
            )


        return (
            "Je ne connais pas encore "
            "ce que vous apprenez."
        )


    # ========================================================
    # PRÉFÉRENCE
    # ========================================================

    if "couleur" in message:

        resultats = [
            souvenir
            for souvenir in souvenirs
            if (
                souvenir.get("categorie") == "preference"
                and "couleur" in souvenir.get(
                    "contenu",
                    ""
                ).lower()
            )
        ]

        if resultats:

            return (
                f"D'après ma mémoire, "
                f"{resultats[-1]['contenu']}."
            )

        return (
            "Je ne connais pas encore "
            "votre couleur préférée."
        )


    if "musique" in message:

        resultats = [
            souvenir
            for souvenir in souvenirs
            if (
                souvenir.get("categorie") == "preference"
                and "musique" in souvenir.get(
                    "contenu",
                    ""
                ).lower()
            )
        ]

        if resultats:

            return (
                f"D'après ma mémoire, "
                f"{resultats[-1]['contenu']}."
            )

        return (
            "Je ne connais pas encore "
            "votre musique préférée."
        )


    # ========================================================
    # IDENTITÉ
    # ========================================================

    if (
        "qui suis-je" in message
        or "mon nom" in message
        or "comment je m'appelle" in message
    ):

        resultats = [
            souvenir
            for souvenir in souvenirs
            if souvenir.get("categorie") == "identite"
        ]

        if resultats:

            return (
                f"D'après ma mémoire, "
                f"{resultats[-1]['contenu']}."
            )

        return (
            "Je ne connais pas encore "
            "votre identité."
        )


    return None