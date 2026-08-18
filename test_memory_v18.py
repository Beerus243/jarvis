from memory import find_semantic_memory


questions = [

    "Quelle technologie gère mon serveur ?",

    "Quelle technologie utilise mon interface ?",

    "Quelle est ma couleur préférée ?",

    "Qu'est-ce que j'aime regarder ?",

    "Avec quel langage ai-je développé le projet ?",

    "Où sont stockées les données ?"

]


print("=" * 60)
print("TEST MÉMOIRE JARVIS V1.8")
print("=" * 60)


for question in questions:

    print()
    print("-" * 60)
    print("Question :", question)
    print("-" * 60)

    souvenir = find_semantic_memory(
        question
    )

    if souvenir:

        print()
        print("✓ SOUVENIR RETENU")
        print()
        print(
            "ID         :",
            souvenir.get("id")
        )

        print(
            "Catégorie  :",
            souvenir.get("categorie")
        )

        print(
            "Contenu    :",
            souvenir.get("contenu")
        )

        print(
            "Importance :",
            souvenir.get("importance")
        )

    else:

        print()
        print("✗ Aucun souvenir suffisamment pertinent")


print()
print("=" * 60)
print("FIN DU TEST")
print("=" * 60)