from memory.project_questions import detect_project_question


questions = [

    "Quel langage utilise mon projet ?",

    "Avec quel langage ai-je développé JARVIS ?",

    "Quel backend utilise mon projet ?",

    "Quelle technologie gère le serveur ?",

    "Avec quoi fonctionne la partie serveur ?",

    "Quel frontend utilise mon projet ?",

    "Quelle technologie gère l'interface ?",

    "Quelle base de données utilise mon projet ?",

    "Où sont stockées les données du projet ?",

    "Quel type de projet est JARVIS ?",

    "Quelle est la stack de mon projet ?",
]


print("================================")
print("TEST QUESTIONS PROJET")
print("================================")

for question in questions:

    result = detect_project_question(
        question
    )

    print()
    print("Question :", question)
    print("Intention :", result)