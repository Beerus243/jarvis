"""Navigation web avec URLs encodées et schémas autorisés."""

import subprocess
from urllib.parse import quote, urlparse


def open_browser():
    try:
        subprocess.Popen(["google-chrome"])
        return True, "J'ouvre ton navigateur."
    except OSError as error:
        return False, f"Impossible d'ouvrir le navigateur : {error}"


def open_url(url):
    parsed = urlparse(str(url))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "URL refusée par la politique de sécurité."
    try:
        subprocess.Popen(["xdg-open", str(url)])
        return True, f"J'ouvre {url}."
    except OSError as error:
        return False, f"Impossible d'ouvrir l'URL : {error}"


def search_web(query):
    return open_url("https://www.google.com/search?q=" + quote(str(query or "").strip()))


def search_wikipedia(query):
    return open_url("https://fr.wikipedia.org/wiki/Special:Recherche?search=" + quote(str(query or "").strip()))
