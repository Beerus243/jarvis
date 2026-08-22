from tools.tools import open_browser, open_musique, get_time
from tools.applications import open_application, open_folder, open_website
from actions.media import play_music
from tools.spotify import play_track, pause, resume, next_track, previous_track
from actions.browser import open_url, search_web, search_wikipedia


def dispatch(intent):

    if isinstance(intent, dict):
        action = intent.get("action")
        if action == "OPEN_APPLICATION":
            return open_application(intent.get("target", ""))[1]
        if action in {"PLAY_MUSIC", "SEARCH_MUSIC"}:
            return play_track(intent.get("title") or intent.get("query"), intent.get("artist"))
        if action == "PAUSE_MUSIC": return pause()
        if action == "RESUME_MUSIC": return resume()
        if action == "NEXT_TRACK": return next_track()
        if action == "PREVIOUS_TRACK": return previous_track()
        if action == "OPEN_URL":
            return open_url(intent.get("url", ""))
        if action == "SEARCH_WEB":
            return search_web(intent.get("query", ""))
        if action == "SEARCH_WIKIPEDIA":
            return search_wikipedia(intent.get("query", ""))

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
