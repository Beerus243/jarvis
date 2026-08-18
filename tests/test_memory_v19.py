from memory import find_semantic_memory


QUESTIONS = [

    "Quelle technologie gère mon serveur ?",

    "Quelle technologie utilise mon interface ?",

    "Quelle est ma couleur préférée ?",

    "Qu'est-ce que j'aime regarder ?",

    "Avec quel langage ai-je développé le projet ?",

    "Où sont stockées les données ?"

]


print("=" * 60)
print("TEST MÉMOIRE JARVIS V1.9")
print("=" * 60)


for question in QUESTIONS:

    print()
    print("-" * 60)

    print(
        f"Question : {question}"
    )

    print("-" * 60)


    souvenir = find_semantic_memory(
        question,
        debug=True
    )


    if souvenir:

        print()

        print(
            "✓ SOUVENIR RETENU"
        )

        print()

        print(
            f"ID         : "
            f"{souvenir.get('id')}"
        )

        print(
            f"Catégorie  : "
            f"{souvenir.get('categorie')}"
        )

        print(
            f"Contenu    : "
            f"{souvenir.get('contenu')}"
        )

        print(
            f"Importance : "
            f"{souvenir.get('importance')}"
        )

    else:

        print()

        print(
            "✗ Aucun souvenir suffisamment pertinent"
        )


print()
print("=" * 60)
print("FIN DU TEST")
print("=" * 60)