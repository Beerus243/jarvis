from intent import detect_intent
from dispatcher import dispatch
from memory_ai import analyze_memory
from personality import speak
from ai import ask_ai


def think(message):

    # 1. Chercher une commande connue
    intent = detect_intent(message)

    if intent:

        response = dispatch(intent)

        if response:
            return response


    # 2. Chercher une information à mémoriser
    memory_response = analyze_memory(message)

    if memory_response:
        return memory_response


    # 3. Vérifier la personnalité de JARVIS
    personality_response = speak(message)

    if personality_response:
        return personality_response


    # 4. Si rien n'a fonctionné → Groq
    return ask_ai(message)