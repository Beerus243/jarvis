from intent import detect_intent
from dispatcher import dispatch
from memory_ai import analyze_memory
from personality import speak
from conversation import add_message
from ai import ask_ai


def think(message):
    """
    Cerveau principal de JARVIS.

    Ordre de traitement :
    1. Enregistrer le message
    2. Chercher une commande connue
    3. Chercher une information à mémoriser
    4. Vérifier la personnalité
    5. Utiliser Groq si rien n'a fonctionné
    """

    # Normaliser le message
    message = message.lower().strip()

    # --------------------------------------------------
    # 1. MÉMOIRE DE CONVERSATION
    # --------------------------------------------------

    add_message("user", message)

    # --------------------------------------------------
    # 2. COMMANDES / INTENTS
    # --------------------------------------------------

    intent = detect_intent(message)

    if intent:

        response = dispatch(intent)

        if response:
            add_message("assistant", response)
            return response

    # --------------------------------------------------
    # 3. MÉMOIRE UTILISATEUR
    # --------------------------------------------------

    memory_response = analyze_memory(message)

    if memory_response:

        add_message("assistant", memory_response)
        return memory_response

    # --------------------------------------------------
    # 4. PERSONNALITÉ
    # --------------------------------------------------

    personality_response = speak(message)

    if personality_response:

        add_message("assistant", personality_response)
        return personality_response

    # --------------------------------------------------
    # 5. INTELLIGENCE ARTIFICIELLE — GROQ
    # --------------------------------------------------

    response = ask_ai(message)

    add_message("assistant", response)

    return response

