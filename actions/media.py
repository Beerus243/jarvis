"""Actions média locales pour Spotify."""

import subprocess
from urllib.parse import quote


def search_music(query):
    query = str(query or "").strip()
    if not query:
        return None
    return f"https://open.spotify.com/search/{quote(query)}"


def play_music(query):
    url = search_music(query)
    if not url:
        return False, "Je n'ai pas compris quel contenu jouer."
    try:
        subprocess.Popen(["xdg-open", url])
        return True, f"Je recherche {query} sur Spotify."
    except OSError as error:
        return False, f"Impossible d'ouvrir Spotify : {error}"
