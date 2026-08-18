THRESHOLD = 0.45

tests = [
    ("Quelle technologie gère mon serveur ?", 0.3710),
    ("Quelle technologie utilise mon interface ?", 0.4221),
    ("Quelle est ma couleur préférée ?", 0.3350),
    ("Qu'est-ce que j'aime regarder ?", 0.6951),
]

for question, score in tests:

    print()
    print("Question :", question)
    print("Score :", score)

    if score >= THRESHOLD:
        print("✓ Pertinent")
    else:
        print("✗ Rejeté")