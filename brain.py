from intent import detect_intent
from dispatcher import dispatch
from memory import analyze_memory, recall_memory
from personality import speak

from conversation import (
    add_message,
    get_context
)

from ai import ask_ai


def think(message):
    # ========================================================
    # 1. AJOUTER LE MESSAGE UTILISATEUR
    # ========================================================
    

    # ========================================================
    # 2. COMMANDES
    # ========================================================

    intent = detect_intent(message)

    if intent:

        response = dispatch(intent)

        if response:

            add_message(
                "assistant",
                response
            )

            return response


    # ========================================================
    # 3. MÉMOIRE LONGUE
    # ========================================================
    memory_response = analyze_memory(message)
    if memory_response:

        add_message(
            "assistant",
            memory_response
        )

        return memory_response



    recall_response = recall_memory(message)

    if recall_response:
        add_message(
            "assistant",
            recall_response
        )

        return recall_response


    # ========================================================
    # 4. RECHERCHE MÉMOIRE
    # ========================================================

    memory_response = recall_memory(message)

    if memory_response:

        add_message(
            "assistant",
            memory_response
        )

        return memory_response


    # ========================================================
    # 5. PERSONNALITÉ
    # ========================================================

    personality_response = speak(message)

    if personality_response:

        add_message(
            "assistant",
            personality_response
        )

        return personality_response


    # ========================================================
    # 6. CONTEXTE
    # ========================================================

    context = get_context()


    # ========================================================
    # 7. GROQ
    # ========================================================

    response = ask_ai(
        message
    )

    add_message(
        "assistant",
        response
    )

    return response