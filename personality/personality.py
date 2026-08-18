def speak(message):

    message = message.lower()

    if "bonjour" in message:
        return "Bonjour Fabrice. Je suis heureux de vous voir."

    elif "merci" in message:
        return "De rien Fabrice. Je suis là pour vous aider."

    elif "comment ca va" in message:
        return "Je fonctionne parfaitement. Merci de vous en inquiéter."

    else:
        return None