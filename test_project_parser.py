from project_parser import parse_project_information


tests = [
    "Le projet est développé en Python",
    "Mon projet utilise Python",
    "J'ai codé le projet avec Python",
    "Le langage utilisé est Python",
    "Le projet est développé en JavaScript",
]


for message in tests:

    result = parse_project_information(message)

    print("Phrase :", message)
    print("Résultat :", result)
    print()