import json
import re
from datetime import datetime

from semantic_memory import (
    similarity,
    create_memory_embedding,
    search_semantic_memory
)


MEMORY_FILE = "user.json"


# ============================================================
# CHARGER LA MÉMOIRE
# ============================================================

def load_memory():

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return {}


# ============================================================
# SAUVEGARDER LA MÉMOIRE
# ============================================================

def save_memory(user):

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            user,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# ID MÉMOIRE
# ============================================================

def generate_memory_id(user):

    souvenirs = user.get(
        "souvenirs",
        []
    )

    if not souvenirs:

        return "s001"

    numbers = []

    for souvenir in souvenirs:

        identifiant = souvenir.get(
            "id",
            ""
        )

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
# MÉMORISER
# ============================================================

def remember(
    contenu,
    categorie,
    importance="moyenne"
):

    user = load_memory()

    if "souvenirs" not in user:

        user["souvenirs"] = []

    # --------------------------------------------------------
    # ÉVITER LES DOUBLONS EXACTS
    # --------------------------------------------------------

    contenu_normalise = contenu.strip().lower()

    for souvenir in user["souvenirs"]:

        ancien = souvenir.get(
            "contenu",
            ""
        ).strip().lower()

        if ancien == contenu_normalise:

            return souvenir

    # --------------------------------------------------------
    # EMBEDDING
    # --------------------------------------------------------

    embedding = create_memory_embedding(
        contenu
    )

    # --------------------------------------------------------
    # SOUVENIR
    # --------------------------------------------------------

    souvenir = {

        "id": generate_memory_id(user),

        "contenu": contenu,

        "categorie": categorie,

        "date": datetime.now().isoformat(),

        "importance": importance,

        "embedding": embedding

    }

    user["souvenirs"].append(
        souvenir
    )

    save_memory(user)

    return souvenir


# ============================================================
# NORMALISATION
# ============================================================

def normalize_text(text):

    text = text.lower()

    text = text.replace(
        "’",
        "'"
    )

    text = re.sub(
        r"[^\w\sàâäéèêëîïôöùûüÿç]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# CONCEPTS
# ============================================================

CONCEPTS = {

    "backend": {
        "mots": [
            "backend",
            "back end",
            "serveur",
            "api",
            "service",
            "fastapi",
            "django",
            "flask",
            "nestjs",
            "node"
        ]
    },

    "frontend": {
        "mots": [
            "frontend",
            "front end",
            "interface",
            "ui",
            "client",
            "react",
            "vue",
            "angular",
            "nextjs",
            "next js"
        ]
    },

    "langage": {
        "mots": [
            "langage",
            "langage de programmation",
            "programmé",
            "programme",
            "programmer",
            "code",
            "codé",
            "python",
            "javascript",
            "typescript",
            "java",
            "c++"
        ]
    },

    "database": {
        "mots": [
            "base de données",
            "base",
            "données",
            "stockées",
            "stockage",
            "database",
            "db",
            "postgresql",
            "mysql",
            "mongodb",
            "sqlite"
        ]
    },

    "preference": {
        "mots": [
            "préfère",
            "préférée",
            "préféré",
            "aime",
            "j'aime",
            "goût",
            "couleur",
            "musique",
            "film",
            "anime"
        ]
    }

}


# ============================================================
# DÉTECTER LES CONCEPTS DE LA QUESTION
# ============================================================

def detect_concepts(message):

    message = normalize_text(
        message
    )

    concepts_detectes = []

    for concept, data in CONCEPTS.items():

        for mot in data["mots"]:

            if mot in message:

                concepts_detectes.append(
                    concept
                )

                break

    return concepts_detectes


# ============================================================
# BONUS CONCEPT
# ============================================================

def concept_bonus(
    question,
    souvenir
):

    concepts = detect_concepts(
        question
    )

    if not concepts:

        return 0.0

    categorie = souvenir.get(
        "categorie",
        ""
    )

    contenu = normalize_text(
        souvenir.get(
            "contenu",
            ""
        )
    )

    bonus = 0.0

    for concept in concepts:

        # ----------------------------------------------------
        # BACKEND
        # ----------------------------------------------------

        if concept == "backend":

            if categorie == "projet":

                if any(
                    mot in contenu
                    for mot in [
                        "backend",
                        "serveur",
                        "api",
                        "fastapi",
                        "django",
                        "flask",
                        "nestjs"
                    ]
                ):

                    bonus += 0.25

        # ----------------------------------------------------
        # FRONTEND
        # ----------------------------------------------------

        elif concept == "frontend":

            if categorie == "projet":

                if any(
                    mot in contenu
                    for mot in [
                        "frontend",
                        "interface",
                        "react",
                        "vue",
                        "angular",
                        "next"
                    ]
                ):

                    bonus += 0.30

        # ----------------------------------------------------
        # LANGAGE
        # ----------------------------------------------------

        elif concept == "langage":

            if any(
                mot in contenu
                for mot in [
                    "python",
                    "javascript",
                    "typescript",
                    "java",
                    "c++"
                ]
            ):

                bonus += 0.30

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        elif concept == "database":

            if any(
                mot in contenu
                for mot in [
                    "postgresql",
                    "mysql",
                    "mongodb",
                    "sqlite",
                    "base de données",
                    "stock"
                ]
            ):

                bonus += 0.30

        # ----------------------------------------------------
        # PRÉFÉRENCE
        # ----------------------------------------------------

        elif concept == "preference":

            if categorie == "preference":

                bonus += 0.30

    return min(
        bonus,
        0.50
    )


# ============================================================
# SCORE LEXICAL
# ============================================================

def lexical_score(
    question,
    contenu
):

    question = normalize_text(
        question
    )

    contenu = normalize_text(
        contenu
    )

    question_words = set(
        question.split()
    )

    contenu_words = set(
        contenu.split()
    )

    if not question_words:

        return 0.0

    mots_communs = (
        question_words
        & contenu_words
    )

    return (
        len(mots_communs)
        / len(question_words)
    )


# ============================================================
# SCORE HYBRIDE
# ============================================================

def calculate_hybrid_score(
    question,
    souvenir
):

    embedding = souvenir.get(
        "embedding"
    )

    if not embedding:

        return 0.0

    question_embedding = (
        create_memory_embedding(
            question
        )
    )

    semantic = similarity(
        question_embedding,
        embedding
    )

    lexical = lexical_score(
        question,
        souvenir.get(
            "contenu",
            ""
        )
    )

    bonus = concept_bonus(
        question,
        souvenir
    )

    # --------------------------------------------------------
    # SCORE FINAL
    # --------------------------------------------------------

    score = (
        semantic * 0.55
        + lexical * 0.20
        + bonus
    )

    return min(
        score,
        1.0
    )


def detect_memory_category(message):

    message = message.lower()

    # --------------------------------------------------------
    # PRÉFÉRENCES
    # --------------------------------------------------------

    if any(
        mot in message
        for mot in [
            "j'aime",
            "j’adore",
            "préféré",
            "préférée",
            "aime regarder",
            "aimes regarder",
            "musique",
            "film",
            "films",
            "anime",
            "animés",
            "couleur"
        ]
    ):
        return "preference"

    # --------------------------------------------------------
    # PROJET
    # --------------------------------------------------------

    if any(
        mot in message
        for mot in [
            "projet",
            "backend",
            "frontend",
            "serveur",
            "interface",
            "technologie",
            "framework",
            "base de données",
            "données"
        ]
    ):
        return "projet"

    # --------------------------------------------------------
    # COMPÉTENCE
    # --------------------------------------------------------

    if any(
        mot in message
        for mot in [
            "apprends",
            "apprendre",
            "apprentissage",
            "étudie",
            "étudier",
            "langage",
            "programmer",
            "programmation"
        ]
    ):
        return "competence"

    # --------------------------------------------------------
    # OBJECTIF
    # --------------------------------------------------------

    if any(
        mot in message
        for mot in [
            "objectif",
            "but",
            "ambition",
            "rêve",
            "veux devenir",
            "veux faire"
        ]
    ):
        return "objectif"

    return None



# ============================================================
# RECHERCHE INTELLIGENTE
# ============================================================

def find_semantic_memory(message):

    user = load_memory()

    souvenirs = user.get(
        "souvenirs",
        []
    )

    if not souvenirs:
        return None

    # --------------------------------------------------------
    # Catégorie recherchée
    # --------------------------------------------------------

    categorie = detect_memory_category(message)

    print(
        f"[MEMORY] Catégorie détectée : {categorie}"
    )

    # --------------------------------------------------------
    # Embedding de la question
    # --------------------------------------------------------

    query_embedding = create_memory_embedding(
        message
    )

    # --------------------------------------------------------
    # Mots importants de la question
    # --------------------------------------------------------

    question_words = set(
        mot.lower().strip("?!.,:;")
        for mot in message.split()
        if len(mot) > 2
    )

    resultats = []

    # --------------------------------------------------------
    # Analyse des souvenirs
    # --------------------------------------------------------

    for souvenir in souvenirs:

        contenu = souvenir.get(
            "contenu",
            ""
        )

        embedding = souvenir.get(
            "embedding"
        )

        if not embedding:
            continue

        contenu_lower = contenu.lower()

        # ----------------------------------------------------
        # SCORE SÉMANTIQUE
        # ----------------------------------------------------

        semantic_score = similarity(
            query_embedding,
            embedding
        )

        # ----------------------------------------------------
        # SCORE LEXICAL
        # ----------------------------------------------------

        mots_contenu = set(
            mot.lower().strip("?!.,:;")
            for mot in contenu.split()
            if len(mot) > 2
        )

        correspondances = (
            question_words
            & mots_contenu
        )

        if question_words:

            lexical_score = (
                len(correspondances)
                / len(question_words)
            )

        else:

            lexical_score = 0

        # ----------------------------------------------------
        # BONUS CATÉGORIE
        # ----------------------------------------------------

        category_bonus = 0

        if (
            categorie
            and souvenir.get("categorie")
            == categorie
        ):

            category_bonus = 0.10

        # ----------------------------------------------------
        # BONUS IMPORTANCE
        # ----------------------------------------------------

        importance_bonus = 0

        importance = souvenir.get(
            "importance",
            "moyenne"
        )

        if importance == "haute":

            importance_bonus = 0.03

        elif importance == "moyenne":

            importance_bonus = 0.01

        # ----------------------------------------------------
        # SCORE FINAL
        # ----------------------------------------------------

        final_score = (
            semantic_score * 0.65
            +
            lexical_score * 0.25
            +
            category_bonus
            +
            importance_bonus
        )

        resultats.append({

            "souvenir": souvenir,

            "semantic_score":
                semantic_score,

            "lexical_score":
                lexical_score,

            "category_bonus":
                category_bonus,

            "importance_bonus":
                importance_bonus,

            "final_score":
                final_score
        })

    # --------------------------------------------------------
    # Trier
    # --------------------------------------------------------

    resultats.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    # --------------------------------------------------------
    # Afficher les meilleurs
    # --------------------------------------------------------

    for resultat in resultats[:5]:

        souvenir = resultat["souvenir"]

        print(
            f"[MEMORY] "
            f"{resultat['semantic_score']:.3f} semantic | "
            f"{resultat['lexical_score']:.3f} lexical | "
            f"{resultat['final_score']:.3f} final | "
            f"{souvenir.get('contenu', '')}"
        )

    # --------------------------------------------------------
    # Aucun résultat
    # --------------------------------------------------------

    if not resultats:

        return None

    meilleur = resultats[0]

    # --------------------------------------------------------
    # SEUIL
    # --------------------------------------------------------

    if meilleur["final_score"] < 0.40:

        print(
            "[MEMORY] "
            "Aucun souvenir suffisamment pertinent"
        )

        return None

    return meilleur["souvenir"]


# ============================================================
# ANALYSER UNE INFORMATION À MÉMORISER
# ============================================================

def analyze_memory(message):

    original_message = message.strip()

    message_lower = (
        original_message.lower()
    )

    # --------------------------------------------------------
    # COULEUR
    # --------------------------------------------------------

    if "ma couleur préférée est" in message_lower:

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
                f"J'ai retenu que votre "
                f"couleur préférée est {value}."
            )

    # --------------------------------------------------------
    # MUSIQUE
    # --------------------------------------------------------

    if "ma musique préférée est" in message_lower:

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
                f"J'ai retenu que votre "
                f"musique préférée est {value}."
            )

    # --------------------------------------------------------
    # PROJET
    # --------------------------------------------------------

    if "je travaille sur" in message_lower:

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
                f"Compris. Je retiens que "
                f"vous travaillez sur {value}."
            )

    # --------------------------------------------------------
    # NOM
    # --------------------------------------------------------

    if "je m'appelle" in message_lower:

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

    if "mon objectif est" in message_lower:

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

    if "j'apprends" in message_lower:

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
# RECHERCHE MÉMOIRE
# ============================================================

def recall_memory(message):

    return find_semantic_memory(
        message
    )


# ============================================================
# EMBEDDINGS MANQUANTS
# ============================================================

def update_missing_embeddings():

    user = load_memory()

    souvenirs = user.get(
        "souvenirs",
        []
    )

    if not souvenirs:

        print(
            "Aucun souvenir à traiter."
        )

        return False

    modified = False

    for souvenir in souvenirs:

        if "embedding" not in souvenir:

            contenu = souvenir.get(
                "contenu",
                ""
            )

            if contenu:

                souvenir[
                    "embedding"
                ] = create_memory_embedding(
                    contenu
                )

                modified = True

    if modified:

        save_memory(
            user
        )

        print(
            "Embeddings ajoutés."
        )

    else:

        print(
            "Tous les souvenirs possèdent "
            "déjà un embedding."
        )

    return modified


# ============================================================
# RECHERCHE SÉMANTIQUE BRUTE
# ============================================================

def search_memory(
    query,
    limit=3
):

    user = load_memory()

    souvenirs = user.get(
        "souvenirs",
        []
    )

    if not souvenirs:

        return []

    return search_semantic_memory(
        query,
        souvenirs,
        limit
    )


# ============================================================
# SYNONYMES CLASSIQUES
# ============================================================

SYNONYMES = {

    "projet": [
        "travail",
        "application",
        "programme",
        "développement",
        "developpement"
    ],

    "python": [
        "programmation",
        "programmer",
        "coder",
        "code"
    ],

    "apprendre": [
        "étudier",
        "etudier",
        "apprentissage",
        "apprends",
        "étudie",
        "etudie"
    ],

    "objectif": [
        "but",
        "ambition",
        "rêve",
        "reve"
    ]

}


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {

    "je",
    "j",
    "mon",
    "ma",
    "mes",
    "le",
    "la",
    "les",
    "un",
    "une",
    "des",
    "de",
    "du",
    "dans",
    "sur",
    "est",
    "quel",
    "quelle",
    "quels",
    "quelles",
    "quoi",
    "que",
    "qui",
    "me",
    "tu",
    "te"

}