from text_normalizer import normalize_text


tests = [
    "Le projet est développé en Python",
    "Le projet est developpé en Python",
    "LE PROJET EST DÉVELOPPÉ EN PYTHON",
]


for text in tests:

    print(
        "Original :",
        text
    )

    print(
        "Normalisé :",
        normalize_text(text)
    )

    print()