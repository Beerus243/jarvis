from tools import open_browser, open_musique, get_time


def dispatch(intent):
    if intent == "GREETINGS":
        return "Bonjour Fabrice. je suis heureux de vous voir."
    elif intent == "GET_TIME":
        heure = get_time()
        return f"Il est actuellement {heure}"

    elif intent == "OPEN_BROWSER":
        return open_browser()

    elif intent == "PLAY_MUSIC":
        return open_musique()

    else:
        return None