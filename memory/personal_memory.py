"""Lecture et mise à jour locale des informations personnelles simples."""

import json
import re

from config.settings import MEMORY_FILE
from memory.text_normalizer import normalize_text


def _normalize_personal_text(message):
    text = normalize_text(message)
    return re.sub(r"[^\w\s]", " ", text)


def load_user_memory():
    """Charge user.json sans jamais faire appel à un service distant."""

    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_user_memory(user):
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(user, file, indent=4, ensure_ascii=False)


def detect_personal_question(message):
    """Reconnaît une question ou une mise à jour personnelle locale."""

    text = _normalize_personal_text(message)
    patterns = (
        "qui suis je",
        "quel est mon nom",
        "comment je m appelle",
        "prenom",
        "tu sais qui je suis",
        "couleur preferee",
        "couleur j aime",
        "aime regarder",
        "regarder quoi",
        "quels contenus j aime",
        "quels sont mes gouts",
        "j aime regarder",
    )
    return any(pattern in text for pattern in patterns)


def _identity_answer(user):
    identity = user.get("identite", {})
    name = identity.get("name") or user.get("name")
    postnom = identity.get("postnom") or user.get("postnom")
    if not name:
        return None
    full_name = f"{name} {postnom}".strip() if postnom else name
    return f"Tu es {full_name}."


def _favorite_color(user):
    preferences = user.get("preferences", {})
    return (
        user.get("couleur_preferee")
        or preferences.get("couleur_preferee")
        or preferences.get("couleur")
    )


def _favorite_content(user):
    preferences = user.get("preferences", {})
    memory = user.get("memory", {})
    return (
        memory.get("aime_regarder")
        or preferences.get("contenus_aimes")
        or preferences.get("films_animes")
        or memory.get("aime")
    )


def _update_watching_preference(message, user):
    original = message.strip()
    match = re.search(
        r"j['’]?aime regarder(?: quoi)?\s+(.+)$",
        original,
        flags=re.IGNORECASE,
    )
    if not match or _normalize_personal_text(original).endswith("quoi"):
        return None

    value = match.group(1).strip()
    if not value:
        return None
    user.setdefault("memory", {})["aime_regarder"] = value
    _save_user_memory(user)
    return f"Je retiens que tu aimes regarder {value}."


def answer_personal_question(message):
    """Répond localement, ou mémorise une préférence personnelle explicite."""

    user = load_user_memory()
    text = _normalize_personal_text(message)

    updated = _update_watching_preference(message, user)
    if updated:
        return updated

    if any(pattern in text for pattern in (
        "qui suis je",
        "quel est mon nom",
        "comment je m appelle",
        "prenom",
        "tu sais qui je suis",
    )):
        return _identity_answer(user)

    if any(pattern in text for pattern in (
        "couleur preferee",
        "couleur j aime",
    )):
        color = _favorite_color(user)
        return f"Ta couleur préférée est {color}." if color else None

    if any(pattern in text for pattern in (
        "aime regarder",
        "regarder quoi",
        "quels contenus j aime",
    )):
        content = _favorite_content(user)
        return f"Tu aimes regarder {content}." if content else None

    if "quels sont mes gouts" in text:
        content = _favorite_content(user)
        color = _favorite_color(user)
        parts = []
        if content:
            parts.append(f"regarder {content}")
        if color:
            parts.append(f"la couleur {color}")
        return "Tu aimes " + " et ".join(parts) + "." if parts else None

    return None
