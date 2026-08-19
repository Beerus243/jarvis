import subprocess
from datetime import datetime


def open_browser():
    subprocess.Popen(["google-chrome"])
    return "J'ouvre ton navigateur."


def open_musique():
    subprocess.Popen([
        "flatpak",
        "run",
        "com.spotify.Client"
    ])
    return "J'ouvre Spotify."


def get_time():
    return datetime.now().strftime("%H:%M:%S")