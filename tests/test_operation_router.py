from core.operation_router import (
    detect_operation,
    READ_MEMORY,
    UPDATE_MEMORY,
    ACTION,
    ASK_AI
)


tests = [
    "Quel backend utilise mon projet ?",
    "Quelle est la stack de mon projet ?",
    "Mon backend utilise FastAPI",
    "Le frontend utilise React",
    "Ouvre Spotify",
    "Quelle heure est-il ?",
    "Pourquoi Python est populaire ?",
    "Explique-moi ce qu'est une API",
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