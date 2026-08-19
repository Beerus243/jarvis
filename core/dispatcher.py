from tools.tools import open_browser, open_musique, get_time
from tools.applications import open_application


def dispatch(intent):

    if intent == "GREETINGS":
        return "Bonjour Fabrice. Je suis heureux de vous voir."

    elif intent == "GET_TIME":
        heure = get_time()
        return f"Il est actuellement {heure}"

    elif intent == "OPEN_BROWSER":
        return open_browser()

    elif intent == "PLAY_MUSIC":
        return open_musique()

    elif intent == "OPEN_TERMINAL":
        success, response = open_application("terminal")
        return response

    elif intent == "OPEN_VSCODE":
        success, response = open_application("vscode")
        return response
    elif intent == "OPEN_FIREFOX":
        success, response = open_application("firefox")
        return response
    
    else:
        return None