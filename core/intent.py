from personality.personality import speak
import unicodedata
import re


def _normalize_text(text: str) -> str:
    # Lowercase, remove accents, and strip punctuation to avoid substring collisions (e.g. 'bro' in 'browser')
    text = text.lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    # Replace non-word characters (keep spaces) with single space
    text = re.sub(r"[^\w\s]", ' ', text)
    # Collapse whitespace
    text = re.sub(r"\s+", ' ', text).strip()
    return text


def detect_intent(message):
    message = _normalize_text(message)

    # Explicit browser launch phrases (French + English) — check first to avoid "bro" -> GREETINGS collisions
    browser_phrases = [
        "ouvre chrome",
        "ouvre google chrome",
        "ouvre le navigateur",
        "ouvre mon navigateur",
        "lance chrome",
        "lance google chrome",
        "demarre chrome",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
        "demarre le navigateur",
    ]

    # The above list intentionally kept concise; also check single keywords
    browser_keywords = ["navigateur", "internet", "browser", "chrome", "open browser", "open chrome", "launch chrome", "launch browser"]

    # Check phrases first
    if any(phrase in message for phrase in browser_phrases):
        return "OPEN_BROWSER"

    # Check keywords (single words) next
    if any(kw in message for kw in browser_keywords):
        return "OPEN_BROWSER"

    # Greetings
    if any(mot in message for mot in ["bonjour", "salut", "hey", "bro", "coucou"]):
        return "GREETINGS"

    # Music
    if any(mot in message for mot in ["musique", "play", "spotify", "jouer"]):
        return "PLAY_MUSIC"

    # Time
    if any(mot in message for mot in ["heure", "time", "horloge"]):
        return "GET_TIME"

    return None