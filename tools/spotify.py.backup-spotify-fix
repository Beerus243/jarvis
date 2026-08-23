"""Contrôle Spotify de JARVIS via Spotify Web API."""

import base64
import json
import os
import subprocess
import time
import urllib.parse
import webbrowser
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from config.spotify import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPES,
    SPOTIFY_TOKEN_FILE,
    validate_config,
)


AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_URL = "https://api.spotify.com/v1"


def _token_path():
    path = Path(SPOTIFY_TOKEN_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_token():
    path = _token_path()

    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return None


def _save_token(token):
    path = _token_path()

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            token,
            file,
            indent=4,
        )


def _build_auth_url(state):
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SPOTIFY_SCOPES,
        "state": state,
    }

    return AUTH_URL + "?" + urllib.parse.urlencode(params)


class _CallbackHandler(BaseHTTPRequestHandler):

    code = None
    state = None
    error = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        _CallbackHandler.code = params.get(
            "code",
            [None],
        )[0]

        _CallbackHandler.state = params.get(
            "state",
            [None],
        )[0]

        _CallbackHandler.error = params.get(
            "error",
            [None],
        )[0]

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8",
        )
        self.end_headers()

        self.wfile.write(
            b"""
            <html>
                <body>
                    <h2>JARVIS Spotify</h2>
                    <p>Authentification terminee.</p>
                    <p>Tu peux fermer cette fenetre.</p>
                </body>
            </html>
            """
        )

    def log_message(self, format, *args):
        return


def _authorize():
    validate_config()

    state = os.urandom(16).hex()

    _CallbackHandler.code = None
    _CallbackHandler.state = None
    _CallbackHandler.error = None

    parsed = urllib.parse.urlparse(
        SPOTIFY_REDIRECT_URI
    )

    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8888

    server = HTTPServer(
        (host, port),
        _CallbackHandler,
    )

    auth_url = _build_auth_url(state)

    print("========================================")
    print("       AUTHENTIFICATION SPOTIFY")
    print("========================================")
    print()
    print("Ouverture de Spotify...")
    print(auth_url)
    print()

    webbrowser.open(auth_url)

    server.handle_request()

    server.server_close()

    if _CallbackHandler.error:
        raise RuntimeError(
            f"Authentification Spotify refusée : "
            f"{_CallbackHandler.error}"
        )

    if not _CallbackHandler.code:
        raise RuntimeError(
            "Aucun code Spotify reçu."
        )

    if _CallbackHandler.state != state:
        raise RuntimeError(
            "Échec de vérification du state OAuth."
        )

    credentials = (
        f"{SPOTIFY_CLIENT_ID}:"
        f"{SPOTIFY_CLIENT_SECRET}"
    )

    encoded = base64.b64encode(
        credentials.encode()
    ).decode()

    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
        },
        data={
            "grant_type": "authorization_code",
            "code": _CallbackHandler.code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
        },
        timeout=15,
    )

    response.raise_for_status()

    token = response.json()

    token["created_at"] = int(time.time())

    _save_token(token)

    return token


def _refresh_token(token):
    refresh_token = token.get("refresh_token")

    if not refresh_token:
        return _authorize()

    credentials = (
        f"{SPOTIFY_CLIENT_ID}:"
        f"{SPOTIFY_CLIENT_SECRET}"
    )

    encoded = base64.b64encode(
        credentials.encode()
    ).decode()

    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=15,
    )

    response.raise_for_status()

    refreshed = response.json()

    if "refresh_token" not in refreshed:
        refreshed["refresh_token"] = refresh_token

    refreshed["created_at"] = int(time.time())

    _save_token(refreshed)

    return refreshed


def _get_token():
    token = _load_token()

    if not token:
        return _authorize()

    created_at = token.get("created_at", 0)
    expires_in = token.get("expires_in", 3600)

    if time.time() >= created_at + expires_in - 60:
        token = _refresh_token(token)

    return token


def _request(method, endpoint, **kwargs):
    token = _get_token()

    headers = kwargs.pop("headers", {})

    headers["Authorization"] = (
        f"Bearer {token['access_token']}"
    )

    response = requests.request(
        method,
        API_URL + endpoint,
        headers=headers,
        timeout=15,
        **kwargs,
    )

    if response.status_code == 401:
        token = _refresh_token(token)

        headers["Authorization"] = (
            f"Bearer {token['access_token']}"
        )

        response = requests.request(
            method,
            API_URL + endpoint,
            headers=headers,
            timeout=15,
            **kwargs,
        )

    return response


def search_track(title=None, artist=None):
    title = str(title or "").strip()
    artist = str(artist or "").strip()

    parts = []

    if title:
        parts.append(
            f'track:"{title}"'
        )

    if artist:
        parts.append(
            f'artist:"{artist}"'
        )

    query = " ".join(parts)

    if not query:
        return None

    response = _request(
        "GET",
        "/search",
        params={
            "q": query,
            "type": "track",
            "limit": 5,
        },
    )

    response.raise_for_status()

    tracks = response.json().get(
        "tracks",
        {},
    ).get(
        "items",
        [],
    )

    if not tracks:
        return None

    return tracks[0]


def get_active_device():
    response = _request(
        "GET",
        "/me/player/devices",
    )

    response.raise_for_status()

    devices = response.json().get(
        "devices",
        [],
    )

    if not devices:
        return None

    active = next(
        (
            device
            for device in devices
            if device.get("is_active")
        ),
        None,
    )

    return active or devices[0]


def play_track(title=None, artist=None):
    track = search_track(
        title=title,
        artist=artist,
    )

    if not track:
        return (
            False,
            "Je n'ai pas trouvé ce morceau sur Spotify.",
        )

    device = get_active_device()

    if not device:
        return (
            False,
            "Aucun appareil Spotify disponible.",
        )

    response = _request(
        "PUT",
        "/me/player/play",
        params={
            "device_id": device["id"],
        },
        json={
            "uris": [track["uri"]],
        },
    )

    if response.status_code not in (200, 204):
        return (
            False,
            f"Spotify a refusé la lecture "
            f"(HTTP {response.status_code}).",
        )

    track_name = track.get(
        "name",
        title or "ce morceau",
    )

    artists = track.get(
        "artists",
        [],
    )

    artist_name = (
        artists[0]["name"]
        if artists
        else artist
    )

    return (
        True,
        f"Je lance {track_name} de {artist_name}.",
    )


def pause():
    response = _request(
        "PUT",
        "/me/player/pause",
    )

    if response.status_code == 204:
        return True, "Je mets Spotify en pause."

    return (
        False,
        f"Impossible de mettre Spotify en pause "
        f"(HTTP {response.status_code}).",
    )


def resume():
    response = _request(
        "PUT",
        "/me/player/play",
    )

    if response.status_code == 204:
        return True, "Je reprends la lecture."

    return (
        False,
        f"Impossible de reprendre Spotify "
        f"(HTTP {response.status_code}).",
    )


def next_track():
    response = _request(
        "POST",
        "/me/player/next",
    )

    if response.status_code == 204:
        return True, "Je passe au morceau suivant."

    return (
        False,
        f"Impossible de passer au morceau suivant "
        f"(HTTP {response.status_code}).",
    )


def previous_track():
    response = _request(
        "POST",
        "/me/player/previous",
    )

    if response.status_code == 204:
        return True, "Je reviens au morceau précédent."

    return (
        False,
        f"Impossible de revenir au morceau précédent "
        f"(HTTP {response.status_code}).",
    )


def open_spotify():
    try:
        subprocess.Popen(
            [
                "flatpak",
                "run",
                "com.spotify.Client",
            ]
        )

        return True, "J'ouvre Spotify."

    except OSError as error:
        return (
            False,
            f"Impossible d'ouvrir Spotify : {error}",
        )