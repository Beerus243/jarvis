import unicodedata
import re
from core.command_understanding import normalize_command, resolve_command_terms


def _normalize_text(text: str) -> str:
    text = text.lower()

    text = unicodedata.normalize("NFD", text)
    text = "".join(
        ch for ch in text
        if not unicodedata.combining(ch)
    )

    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def detect_intent(message):

    message = _normalize_text(resolve_command_terms(message)["normalized_terms"])

    # Les phrases interrogatives générales ne sont pas des commandes locales.
    if message.startswith(("pourquoi ", "comment ", "qu est ce ", "est ce que ")):
        return None

    # ========================================================
    # CHROME / NAVIGATEUR
    # ========================================================

    chrome_phrases = [
        "ouvre chrome",
        "ouvre google chrome",
        "lance chrome",
        "lance google chrome",
        "demarre chrome",
        "demarre google chrome",
        "ouvre internet",
        "open chrome",
        "open browser",
        "launch chrome",
        "ouvre le navigateur",
        "ouvre mon navigateur",
        "lance le navigateur",
        "lance mon navigateur",
    ]

    if any(
        phrase in message
        for phrase in chrome_phrases
    ):
        return "OPEN_BROWSER"

    # ========================================================
    # SPOTIFY
    # ========================================================

    spotify_phrases = [
        "ouvre spotify",
        "lance spotify",
        "demarre spotify",
        "ouvre la musique",
        "lance la musique",
    ]

    if any(
        phrase in message
        for phrase in spotify_phrases
    ):
        return "OPEN_SPOTIFY"


    # ========================================================
    # LECTURE D'UN ARTISTE (PLAY_MUSIC avec artiste)
    # ========================================================

    play_music_match = re.match(
        r"^(?:mets|joue)(?: moi)?(?: du| de la| des)? (.+)$",
        message,
    )

    if play_music_match:
        artist = play_music_match.group(1).strip()
        if artist:
            return {"action": "PLAY_MUSIC", "artist": artist}
        
    # ========================================================
    # FIREFOX
    # ========================================================

    firefox_phrases = [
        "ouvre firefox",
        "lance firefox",
        "demarre firefox",
    ]

    if any(
        phrase in message
        for phrase in firefox_phrases
    ):
        return "OPEN_FIREFOX"

    # ========================================================
    # VISUAL STUDIO CODE
    # ========================================================

    vscode_phrases = [
        "ouvre visual studio code",
        "lance visual studio code",
        "demarre visual studio code",
        "ouvre vscode",
        "lance vscode",
        "demarre vscode",
        "ouvre vs code",
        "lance vs code",
    ]

    if any(
        phrase in message
        for phrase in vscode_phrases
    ):
        return "OPEN_VSCODE"

    # ========================================================
    # TERMINAL
    # ========================================================

    terminal_phrases = [
        "ouvre le terminal",
        "ouvre terminal",
        "lance le terminal",
        "lance terminal",
        "demarre le terminal",
        "demarre terminal",
        "ouvre konsole",
        "lance konsole",
    ]

    if any(
        phrase in message
        for phrase in terminal_phrases
    ):
        return "OPEN_TERMINAL"

    if "ouvre" in message and any(value in message for value in ("dossier", "documents", "repertoire", "répertoire")):
        return "OPEN_FOLDER"
    if "ouvre" in message and any(value in message for value in ("site", "youtube", "github", "google")):
        return "OPEN_WEBSITE"

    # ========================================================
    # SALUTATIONS
    # ========================================================

    greetings = [
        "bonjour",
        "salut",
        "hey",
        "bro",
        "coucou",
    ]

    if any(
        mot in message.split()
        for mot in greetings
    ):
        return "GREETINGS"

    # ========================================================
    # HEURE
    # ========================================================

    if any(
        mot in message.split()
        for mot in [
            "heure",
            "time",
            "horloge",
        ]
    ):
        return "GET_TIME"

    # ========================================================
    # COMPATIBILITÉ ANCIEN SYSTÈME
    # ========================================================

    if any(
        mot in message.split()
        for mot in [
            "navigateur",
            "internet",
            "browser",
        ]
    ):
        return "OPEN_BROWSER"

    if any(
        mot in message.split()
        for mot in [
            "musique",
            "spotify",
        ]
    ):
        return "OPEN_SPOTIFY"

    return None
