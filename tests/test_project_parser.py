from memory.project_parser import parse_project_information


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
print(
    parse_project_information(
        "Quel backend utilise mon projet ?"
    )
)

print(
    parse_project_information(
        "Quelle technologie gère le serveur ?"
    )
)

print(
    parse_project_information(
        "Mon backend utilise Django"
    )
)

print(
    parse_project_information(
        "Le frontend utilise React"
    )
)