from personality import speak

def detect_intent(message):
    message = message.lower()

    if any (mot in message for mot in ["bonjour", "salut","hey","bro" "coucou"]):
        return "GREETINGS"

    elif any (mot in message for mot in ["musique", "play", "spotify", "jouer"]):
        return "PLAY_MUSIC"

    elif any (mot in message for mot in ["heure", "time", "horloge"]):
        return "GET_TIME"
    elif any (mot in message for mot in ["navigateur", "internet", "browser"]):
        return "OPEN_BROWSER"