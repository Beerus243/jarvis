from intent import detect_intent
from dispatcher import dispatch

from memory import (
    analyze_memory,
    recall_memory,
    search_memory
)

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

    add_message(
        "user",
        message
    )


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


    # ========================================================
    # 4. RECHERCHE SÉMANTIQUE
    # ========================================================

    semantic_results = search_memory(
        message,
        limit=3
    )

    if semantic_results:

        best_memory = semantic_results[0]

        score = best_memory["score"]
        souvenir = best_memory["souvenir"]


        # ----------------------------------------------------
        # Seuil de confiance
        # ----------------------------------------------------

        if score >= 0.45:

            response = (
                f"D'après ma mémoire, "
                f"{souvenir.get('contenu')}"
            )

            add_message(
                "assistant",
                response
            )

            return response


    # ========================================================
    # 5. RECHERCHE MÉMOIRE CLASSIQUE
    # ========================================================

    memory_response = recall_memory(message)

    if memory_response:

        add_message(
            "assistant",
            memory_response
        )

        return memory_response


    # ========================================================
    # 6. PERSONNALITÉ
    # ========================================================

    personality_response = speak(message)

    if personality_response:

        add_message(
            "assistant",
            personality_response
        )

        return personality_response


    # ========================================================
    # 7. CONTEXTE
    # ========================================================

    context = get_context()


    # ========================================================
    # 8. GROQ
    # ========================================================

    response = ask_ai(
        message
    )

    add_message(
        "assistant",
        response
    )

    return response