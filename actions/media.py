"""Actions média locales pour Spotify."""

from tools.spotify import (
    open_spotify,
    search_track,
    play_track,
    pause,
    resume,
    next_track,
    previous_track,
)


def search_music(query):
    """Recherche un morceau ou artiste sur Spotify."""

    query = str(query or "").strip()

    if not query:
        return False, "Je n'ai rien à rechercher sur Spotify."

    track = search_track(title=query)

    if not track:
        return False, "Je n'ai trouvé aucun résultat sur Spotify."

    return True, track


def play_music(artist=None, title=None, query=None):
    """Recherche et lance directement un morceau Spotify."""

    # Compatibilité avec les anciennes commandes utilisant query.
    if query and not title:
        title = query

    if not title and not artist:
        return False, "Je ne sais pas quoi jouer sur Spotify."

    return play_track(
        title=title,
        artist=artist,
    )


def open_music():
    """Ouvre le client Spotify."""

    return open_spotify()


def pause_music():
    return pause()


def resume_music():
    return resume()


def next_music():
    return next_track()


def previous_music():
    return previous_track()