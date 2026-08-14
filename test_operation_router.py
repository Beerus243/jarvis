from operation_router import (
    detect_operation,
    READ_MEMORY,
    UPDATE_MEMORY,
    ASK_AI
)


tests = [
    "Quel backend utilise mon projet ?",
    "Quelle technologie gère le serveur ?",
    "Quelle est la stack de mon projet ?",
    "Mon backend utilise FastAPI",
    "Le frontend utilise React",
    "Le projet est développé en Python",
    "Pourquoi Python est-il populaire ?",
    "Explique-moi ce qu'est une API"
]


print("================================")
print("TEST OPERATION ROUTER")
print("================================")


for message in tests:

    operation = detect_operation(
        message
    )

    print()
    print("Message :", message)
    print("Opération :", operation)