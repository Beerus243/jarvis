"""Contrôle Spotify local, sans dépendance réseau obligatoire."""

import subprocess
from urllib.parse import quote


def open_spotify():
    try:
        subprocess.Popen(["flatpak", "run", "com.spotify.Client"])
        return True, "J'ouvre Spotify."
    except OSError as error:
        return False, f"Impossible d'ouvrir Spotify : {error}"


def search_spotify(query):
    query = str(query or "").strip()
    return "https://open.spotify.com/search/" + quote(query) if query else None


def play_track(title=None, artist=None):
    query = " ".join(value for value in (title, artist) if value).strip()
    if not query:
        return False, "Je n'ai pas compris quel morceau jouer."
    try:
        # URI Spotify : le système l'associe à l'application Spotify,
        # contrairement à une URL https qui ouvre le navigateur.
        subprocess.Popen(["xdg-open", "spotify:search:" + quote(query)])
        label = f"{title} de {artist}" if title and artist else (title or artist)
        return True, f"Je lance la recherche de {label} dans Spotify."
    except OSError as error:
        return False, f"Impossible de lancer Spotify : {error}"


def _playerctl(command):
    try:
        completed = subprocess.run(["playerctl", command], capture_output=True, text=True)
        return completed.returncode == 0, "Commande Spotify exécutée." if completed.returncode == 0 else "Spotify n'a pas accepté la commande."
    except OSError as error:
        return False, f"Contrôle Spotify indisponible : {error}"


def pause(): return _playerctl("pause")
def resume(): return _playerctl("play")
def next_track(): return _playerctl("next")
def previous_track(): return _playerctl("previous")
