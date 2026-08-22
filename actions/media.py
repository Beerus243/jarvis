"""Actions média locales pour Spotify."""

from tools.spotify import play_track, search_spotify


def search_music(query):
    return search_spotify(query)


def play_music(query):
    return play_track(title=query)
