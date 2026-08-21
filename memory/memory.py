import json
import re
import unicodedata
from datetime import datetime

from config.settings import EMBEDDING_DIMENSION, MEMORY_FILE


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

    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

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

    from memory.semantic_memory import create_memory_embedding

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

    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(
        character
        for character in text
        if unicodedata.category(character) != "Mn"
    )

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
# RANKING HYBRIDE ET RECHERCHE MÉMOIRE
# ============================================================

from config.settings import (
    CATEGORY_WEIGHT,
    LEXICAL_WEIGHT,
    SEMANTIC_THRESHOLD,
    SEMANTIC_WEIGHT,
    SPECIFICITY_WEIGHT,
)


QUERY_TOPICS = {
    "backend": {
        "backend", "back end", "serveur", "cote serveur", "api",
        "fastapi", "django", "flask", "nestjs", "express",
    },
    "frontend": {
        "frontend", "front end", "interface", "interface utilisateur",
        "ui", "cote client", "react", "vue", "angular", "next",
    },
    "database": {
        "base de donnees", "base de donnee", "database", "bdd", "donnees",
        "stockage", "stockees", "postgresql", "postgres", "mysql",
        "mongodb", "sqlite",
    },
    "language": {
        "langage", "language", "programme", "programmer", "code",
        "developpe", "developper", "python", "javascript", "typescript",
        "java",
    },
    "watching": {
        "aime regarder", "aimes regarder", "regarder", "films", "film",
        "anime", "animes", "series", "serie",
    },
    "color": {"couleur", "color"},
}


TOPIC_CONTENT_TERMS = {
    "backend": {"backend", "serveur", "api", "fastapi", "django", "flask", "nestjs", "express"},
    "frontend": {"frontend", "interface", "ui", "react", "vue", "angular", "next"},
    "database": {"donnees", "stockage", "stockees", "postgresql", "postgres", "mysql", "mongodb", "sqlite"},
    "language": {"langage", "programme", "code", "developpe", "python", "javascript", "typescript", "java"},
    "watching": {"regarder", "film", "films", "anime", "animes", "serie", "series"},
    "color": {"couleur", "jaune", "bleu", "rouge", "vert", "noir", "blanc"},
}


def detect_query_topics(message):
    """Retourne les sujets explicites de la question, sans deviner."""

    text = normalize_text(message)
    return {
        topic
        for topic, terms in QUERY_TOPICS.items()
        if any(term in text for term in terms)
    }


def detect_memory_category(message):
    """Détermine la catégorie attendue par une question."""

    topics = detect_query_topics(message)
    if topics & {"watching", "color"}:
        return "preference"
    if topics & {"backend", "frontend", "database", "language"}:
        return "projet"
    if any(term in normalize_text(message) for term in ("objectif", "but", "ambition")):
        return "objectif"
    if any(term in normalize_text(message) for term in ("apprendre", "apprends", "competence")):
        return "competence"
    if any(term in normalize_text(message) for term in ("qui suis je", "mon nom", "appelle")):
        return "identite"
    return None


def lexical_score(question, contenu):
    """Mesure les mots informatifs communs entre question et souvenir."""

    question_words = {
        word for word in normalize_text(question).split()
        if len(word) > 2 and word not in STOP_WORDS
    }
    content_words = set(normalize_text(contenu).split())
    if not question_words:
        return 0.0
    return len(question_words & content_words) / len(question_words)


def calculate_specificity(question, contenu):
    """Mesure si le souvenir parle du sujet précis demandé."""

    topics = detect_query_topics(question)
    if not topics:
        return 0.0
    content = set(normalize_text(contenu).split())
    matches = sum(
        1 for topic in topics
        if content & TOPIC_CONTENT_TERMS[topic]
    )
    return matches / len(topics)


def calculate_hybrid_score(question, souvenir):
    """Calcule le score explicable utilisé par la recherche mémoire."""

    from memory.semantic_memory import create_memory_embedding, similarity

    embedding = souvenir.get("embedding")
    contenu = souvenir.get("contenu", "")
    if not isinstance(embedding, list) or not embedding or not contenu:
        return None

    semantic = max(0.0, similarity(create_memory_embedding(question), embedding))
    lexical = lexical_score(question, contenu)
    category = 0.0
    expected_category = detect_memory_category(question)
    if expected_category and souvenir.get("categorie") == expected_category:
        category = 1.0
    specificity = calculate_specificity(question, contenu)

    final = (
        semantic * SEMANTIC_WEIGHT
        + lexical * LEXICAL_WEIGHT
        + category * CATEGORY_WEIGHT
        + specificity * SPECIFICITY_WEIGHT
    )
    return {
        "souvenir": souvenir,
        "semantic": semantic,
        "lexical": lexical,
        "category": category,
        "specificity": specificity,
        "final": final,
    }


def find_semantic_memory(message, debug=False):
    """Retourne le meilleur souvenir fiable ou ``None``."""

    souvenirs = load_memory().get("souvenirs", [])
    candidates = [
        scored for souvenir in souvenirs
        if (scored := calculate_hybrid_score(message, souvenir)) is not None
    ]
    candidates.sort(key=lambda item: item["final"], reverse=True)

    if debug:
        print(f"[MEMORY] Catégorie détectée : {detect_memory_category(message)}")
        for item in candidates[:5]:
            print(
                f"[MEMORY] {item['semantic']:.3f} semantic | "
                f"{item['lexical']:.3f} lexical | "
                f"{item['category']:.3f} category | "
                f"{item['specificity']:.3f} specificity | "
                f"{item['final']:.3f} final | {item['souvenir'].get('contenu', '')}"
            )

    if not candidates or candidates[0]["final"] < SEMANTIC_THRESHOLD:
        return None
    return candidates[0]["souvenir"]


def find_best_memory(message, debug=False):
    """Alias public conservé pour les anciens appelants."""

    return find_semantic_memory(message, debug=debug)


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

    from memory.semantic_memory import create_memory_embedding

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

        embedding = souvenir.get("embedding")
        valid_embedding = (
            isinstance(embedding, list)
            and len(embedding) == EMBEDDING_DIMENSION
            and all(isinstance(value, (int, float)) for value in embedding)
        )
        if valid_embedding:
            continue

        contenu = souvenir.get("contenu", "")
        if contenu:
            souvenir["embedding"] = create_memory_embedding(contenu)
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

    from memory.semantic_memory import search_semantic_memory

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
