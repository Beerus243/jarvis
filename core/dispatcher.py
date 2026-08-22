from tools.tools import open_browser, open_musique, get_time
from tools.applications import open_application, open_folder, open_website


def dispatch(intent):

    if intent == "GREETINGS":
        return "Bonjour Fabrice. Je suis heureux de vous voir."

    elif intent == "GET_TIME":
        heure = get_time()
        return f"Il est actuellement {heure}"

    elif intent == "OPEN_BROWSER":
        return open_browser()

    elif intent == "OPEN_SPOTIFY":
        return open_musique()

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
    elif intent == "OPEN_FOLDER":
        return open_folder("Documents")
    elif intent in {"OPEN_SITE", "OPEN_WEBSITE"}:
        return open_website("https://www.google.com")
    
    else:
        return None
