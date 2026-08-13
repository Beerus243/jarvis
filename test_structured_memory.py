from structured_memory import answer_project_question


questions = [
    "Quelle technologie gère le serveur ?",
"Quelle technologie gère l'interface ?",
"Quelle technologie stocke les données ?",
"Avec quel langage ai-je développé JARVIS ?",
]


print("================================")
print("TEST MÉMOIRE STRUCTURÉE")
print("================================")

for question in questions:

    print()
    print("Question :", question)

    response = answer_project_question(
        question
    )

    print("Réponse :", response)