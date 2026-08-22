"""Navigation Web locale, contrôlée et testable."""

import subprocess
from urllib.parse import quote, urlparse

ALLOWED_HOSTS = {
    "www.google.com", "www.wikipedia.org", "fr.wikipedia.org",
    "www.youtube.com", "open.spotify.com", "github.com", "www.github.com",
}


def open_browser():
    try:
        subprocess.Popen(["google-chrome"])
        return True, "J'ouvre ton navigateur."
    except OSError as error:
        return False, f"Impossible d'ouvrir le navigateur : {error}"


def open_url(url):
    parsed = urlparse(str(url or ""))
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in ALLOWED_HOSTS:
        return False, "URL refusée par la politique de sécurité."
    try:
        subprocess.Popen(["xdg-open", str(url)])
        return True, f"J'ouvre {url}."
    except OSError as error:
        return False, f"Impossible d'ouvrir l'URL : {error}"


def search_web(query):
    query = str(query or "").strip()
    if not query:
        return False, "La recherche est vide."
    return open_url("https://www.google.com/search?q=" + quote(query))


def search_wikipedia(query):
    query = str(query or "").strip()
    if not query:
        return False, "La recherche Wikipédia est vide."
    return open_url("https://fr.wikipedia.org/wiki/Sp%C3%A9cial:Recherche?search=" + quote(query))
