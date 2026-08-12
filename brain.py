from intent import detect_intent
from dispatcher import dispatch
from structured_memory import analyze_project_information
from reference import resolve_reference

from memory import (
    analyze_memory,
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

    resolved_reference = resolve_reference(message)

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
# 3.5 MÉMOIRE STRUCTURÉE
# ========================================================

    structured_response = analyze_project_information(message)

    if structured_response:

        add_message(
        "assistant",
        structured_response
    )

    return structured_response


    # ========================================================
    # 4. RECHERCHE SÉMANTIQUE
    # ========================================================
    semantic_results = search_memory(message,limit=3)
    memory_context = "" 

    for result in semantic_results:
        score = result["score"]
        souvenir = result["souvenir"]

        if score >= 0.45:
            contenu = souvenir.get("contenu","")
            memory_context += (
            f"- {contenu}\n"
        )
    # ========================================================
    # 5. RECHERCHE MÉMOIRE CLASSIQUE
    # ========================================================




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
        resolved_reference, memory_context
    )

    add_message(
        "assistant",
        response
    )

    return response