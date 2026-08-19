import unicodedata
import re


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

    message = _normalize_text(message)

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
