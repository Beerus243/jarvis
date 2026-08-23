import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

SPOTIFY_REDIRECT_URI = os.getenv(
    "SPOTIFY_REDIRECT_URI",
    "http://127.0.0.1:8888/callback",
)


SPOTIFY_SCOPES = " ".join(
    [
        "user-read-playback-state",
        "user-read-currently-playing",
        "user-modify-playback-state",
    ]
)


SPOTIFY_TOKEN_FILE = PROJECT_ROOT / "data" / "spotify_token.json"


def validate_config():
    missing = []

    if not SPOTIFY_CLIENT_ID:
        missing.append("SPOTIFY_CLIENT_ID")

    if not SPOTIFY_CLIENT_SECRET:
        missing.append("SPOTIFY_CLIENT_SECRET")

    if not SPOTIFY_REDIRECT_URI:
        missing.append("SPOTIFY_REDIRECT_URI")

    if missing:
        raise RuntimeError(
            "Configuration Spotify incomplète : "
            + ", ".join(missing)
        )