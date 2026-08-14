from intent import detect_intent
from dispatcher import dispatch

from operation_router import (
    detect_operation,
    READ_MEMORY,
    UPDATE_MEMORY,
    ACTION,
    ASK_AI
)

from structured_memory import (
    analyze_project_update,
    answer_project_question
)

from reference import resolve_reference

from memory import (
    analyze_memory,
    search_memory
)

from personality import speak

from conversation import add_message

from ai import ask_ai


def think(message):

    # ========================================================
    # 1. DÉTERMINER L'OPÉRATION
    # ========================================================

    operation = detect_operation(message)

    # ========================================================
    # 2. RÉSOUDRE LES RÉFÉRENCES
    # ========================================================

    resolved_reference = resolve_reference(message)

    # ========================================================
    # 3. AJOUTER LE MESSAGE UTILISATEUR À L'HISTORIQUE
    # ========================================================

    add_message(
        "user",
        message
    )

    # ========================================================
    # 4. ACTION
    # ========================================================

    if operation == ACTION:

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
    # 5. MISE À JOUR DE LA MÉMOIRE
    # ========================================================

    if operation == UPDATE_MEMORY:

        response = analyze_project_update(
            message
        )

        if response:

            add_message(
                "assistant",
                response
            )

            return response

    # ========================================================
    # 6. LECTURE DE LA MÉMOIRE STRUCTURÉE
    # ========================================================

    if operation == READ_MEMORY:

        response = answer_project_question(
            resolved_reference
        )

        if response:

            add_message(
                "assistant",
                response
            )

            return response

    # ========================================================
    # 7. MÉMOIRE LONGUE CLASSIQUE
    # ========================================================

    memory_response = analyze_memory(
        message
    )

    if memory_response:

        add_message(
            "assistant",
            memory_response
        )

        return memory_response

    # ========================================================
    # 8. RECHERCHE SÉMANTIQUE
    # ========================================================

    semantic_results = search_memory(
        resolved_reference,
        limit=3
    )

    memory_context = ""

    for result in semantic_results:

        score = result["score"]
        souvenir = result["souvenir"]

        if score >= 0.45:

            contenu = souvenir.get(
                "contenu",
                ""
            )

            memory_context += (
                f"- {contenu}\n"
            )

    # ========================================================
    # 9. PERSONNALITÉ
    # ========================================================

    personality_response = speak(
        message
    )

    if personality_response:

        add_message(
            "assistant",
            personality_response
        )

        return personality_response

    # ========================================================
    # 10. INTELLIGENCE ARTIFICIELLE
    # ========================================================

    response = ask_ai(
        resolved_reference,
        memory_context
    )

    add_message(
        "assistant",
        response
    )

    return response