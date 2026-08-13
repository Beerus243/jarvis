from project_parser import parse_project_information


tests = [
    "Le projet est développé en Python",
    "Mon projet utilise Python",
    "J'ai codé le projet avec Python",

    "Le backend utilise FastAPI",
    "Le backend utilise Django",

    "Le projet utilise PostgreSQL",
    "Ma base de données est MongoDB",

    "Le frontend utilise React",
    "Le frontend est développé avec Next.js",
]

for phrase in tests:

    result = parse_project_information(phrase)

    print("Phrase :", phrase)
    print("Résultat :", result)
    print()