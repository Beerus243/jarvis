from structured_memory import answer_project_question


questions = [
    "Quel langage utilise mon projet ?",
    "Quel backend utilise mon projet ?",
    "Quel frontend utilise mon projet ?",
    "Quelle base de données utilise mon projet ?"
]


for question in questions:

    print()
    print("Question :", question)

    response = answer_project_question(
        question
    )

    print("Réponse :", response)