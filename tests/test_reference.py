from core.reference import has_reference


tests = [
    "Mon backend utilise FastAPI",
    "Il est développé en Python",
    "Ce projet utilise PostgreSQL",
    "Quel backend utilise mon projet ?",
    "Elle utilise React",
    "Maintenant mon backend utilise Django"
]


for phrase in tests:

    print(
        phrase,
        "=>",
        has_reference(phrase)
    )