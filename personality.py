def speak(message):
    message = message.lower()

    if "bonjour" in message:
        return "Bonjour Fabrice. je suis heureux de vous voir."

    elif "merci" in message:
        return "De rien, Monsieur. Je suis là pour vous aider."
    elif "verifie" in message:
        return "Je vais vérifier cela pour vous."
    elif "comment ca va aujourd'hui" in message:
        return "Je vais bien, merci. j'attends vos ordres?"
    else:
        return None