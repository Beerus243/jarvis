def detect_wake_word(message):

    if not message:
        return False

    message = message.lower()

    wake_words = [
        "jarvis",
        "hé jarvis",
        "hey jarvis",
        "ok jarvis",
        "jarvis écoute-moi"
    ]

    for word in wake_words:

        if word in message:
            return True

    return False