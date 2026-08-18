from semantic_memory import (
    create_memory_embedding,
    search_semantic_memory
)


print("================================")
print("TEST RECHERCHE SÉMANTIQUE")
print("================================")


# ============================================================
# SOUVENIRS
# ============================================================

souvenirs = [

    {
        "contenu": "Mon backend utilise FastAPI."
    },

    {
        "contenu": "Le frontend de JARVIS utilise React."
    },

    {
        "contenu": "Le projet est développé en Python."
    },

    {
        "contenu": "J'utilise PostgreSQL pour stocker les données."
    },

    {
        "contenu": "J'aime regarder des films et des animés."
    }
]


# ============================================================
# CRÉER LES EMBEDDINGS
# ============================================================

for souvenir in souvenirs:

    souvenir["embedding"] = create_memory_embedding(
        souvenir["contenu"]
    )


# ============================================================
# QUESTIONS
# ============================================================

questions = [

    "Quelle technologie gère mon serveur ?",

    "Avec quel langage ai-je développé le projet ?",

    "Où sont stockées les données ?",

    "Quelle technologie utilise mon interface ?",

    "Qu'est-ce que j'aime regarder ?"
]


# ============================================================
# RECHERCHE
# ============================================================

for question in questions:

    print()
    print("Question :", question)

    results = search_semantic_memory(
        question,
        souvenirs,
        limit=3
    )

    for result in results:

        print(
            f"{result['score']:.4f}",
            "→",
            result["souvenir"]["contenu"]
        )