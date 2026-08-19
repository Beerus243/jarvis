from core.intent import detect_intent
from core.dispatcher import dispatch

from core.operation_router import (
    detect_operation,
    READ_MEMORY,
    UPDATE_MEMORY,
    ACTION,
    ASK_AI,
    PERSONAL_MEMORY,
)

from memory.structured_memory import (
    analyze_project_update,
    answer_project_question
)

from core.reference import resolve_reference

from memory import (
    analyze_memory,
    find_semantic_memory
)
from memory.personal_memory import answer_personal_question

from personality.personality import speak

from core.conversation import add_message

from ai.ai import ask_ai


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
    # 7. MÉMOIRE PERSONNELLE LOCALE
    # ========================================================

    if operation == PERSONAL_MEMORY:

        personal_response = answer_personal_question(message)

        if personal_response:

            add_message(
                "assistant",
                personal_response
            )

            return personal_response

    # ========================================================
    # 8. MÉMOIRE LONGUE CLASSIQUE
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
    # 9. RECHERCHE SÉMANTIQUE
    # ========================================================

    memory_context = ""
    relevant_memory = find_semantic_memory(
        resolved_reference,
        debug=False,
    )
    if relevant_memory:
        memory_context = f"- {relevant_memory.get('contenu', '')}\n"

    # ========================================================
    # 10. PERSONNALITÉ
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
    # 11. INTELLIGENCE ARTIFICIELLE
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
