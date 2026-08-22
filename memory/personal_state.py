"""Mémoire locale de l'état actuel de Fabrice."""

import json
import re
from datetime import datetime

from config.settings import MEMORY_FILE
from memory.text_normalizer import normalize_text


_ACTIVITY_PATTERNS = (
    ("sleeping", ("je vais dormir", "je pars dormir", "je vais me coucher", "je vais faire dodo", "je vais au lit", "je dors", "je suis en train de dormir")),
    ("eating", ("je vais manger", "je vais déjeuner", "je vais dejeuner", "je vais dîner", "je vais diner", "je vais prendre le petit dejeuner", "je vais prendre mon petit dejeuner", "je pars manger", "je suis en train de manger", "je mange")),
    ("outside", ("je sors", "je vais sortir", "je vais dehors", "je quitte la maison", "je vais en ville", "je vais au travail", "je vais a l ecole", "je vais a la salle", "je suis dehors", "je pars")),
    ("working", ("je vais travailler",)),
    ("studying", ("je vais étudier", "je vais etudier")),
    ("gaming", ("je vais jouer",)),
    ("home", ("je rentre", "je suis rentré", "je suis rentre", "je viens de rentrer", "je suis de retour", "je suis à la maison", "je suis a la maison", "je suis revenu")),
    ("awake", ("je me réveille", "je me reveille", "je viens de me réveiller", "je viens de me reveiller", "je suis réveillé", "je suis reveille", "je suis réveillé maintenant", "je suis reveille maintenant")),
)

_QUESTION_MARKERS = (
    "qu est ce que je fais",
    "je fais quoi",
    "quelle est mon activite",
    "depuis quand je travaille",
    "depuis quand je dors",
    "suis je disponible",
    "ou suis je",
    "est ce que je dors",
    "je dors depuis combien",
    "quand ai je commence a dormir",
    "quel est mon etat actuel",
    "est ce que je mange",
    "je mange depuis combien",
    "depuis quand je mange",
    "est ce que je travaille",
    "est ce que j etudie",
    "depuis combien de temps je travaille",
    "depuis combien de temps j etudie",
    "quand ai je commence a travailler",
    "quand ai je commence a etudier",
    "est ce que je joue",
    "est ce que je regarde",
    "qu est ce que je regarde",
    "est ce que j ecoute",
    "depuis combien de temps je joue",
    "depuis combien de temps je regarde",
    "depuis combien de temps j ecoute",
    "est ce que je suis dehors",
    "ou suis je actuellement",
    "est ce que je suis a la maison",
    "depuis combien de temps je suis dehors",
    "quand suis je sorti",
)

_FINISHED_EATING = (
    "j ai fini de manger",
    "je viens de finir",
    "j ai termine de manger",
    "je ne mange plus",
)

_FINISHED_WORKING = ("j ai fini de travailler", "j arrete de travailler", "je ne travaille plus")
_FINISHED_STUDYING = ("j ai fini d etudier", "j arrete d etudier", "j ai fini mes etudes")
_FINISHED_PLAYING = ("j ai fini de jouer", "j arrete de jouer")
_FINISHED_WATCHING = ("j ai fini le film", "j ai fini l anime", "j arrete de regarder")
_FINISHED_LISTENING = ("j ai fini d ecouter de la musique", "j arrete la musique")


def _load():
    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _save(data):
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def _text(message):
    return re.sub(r"[^\w\s]", " ", normalize_text(message))


def detect_personal_state(message):
    """Retourne la mise à jour d'état détectée, ou ``None``."""
    text = _text(message)
    if detect_personal_state_question(message):
        return None
    if any(phrase in text for phrase in _FINISHED_EATING):
        return {"activity": "awake", "availability": "available"}
    if any(phrase in text for phrase in _FINISHED_WORKING + _FINISHED_STUDYING):
        return {"activity": "awake", "availability": "available"}
    if any(phrase in text for phrase in _FINISHED_PLAYING + _FINISHED_WATCHING + _FINISHED_LISTENING):
        return {"activity": "awake", "availability": "available"}

    # Une activité explicite reste prioritaire, même lorsqu'elle implique
    # un déplacement (ex. « je vais sortir travailler »).
    if text.startswith("je vais sortir ") or text.startswith("je pars "):
        for activity, words in (
            ("sleeping", ("dormir", "coucher")),
            ("eating", ("manger", "dejeuner", "diner")),
            ("working", ("travailler",)),
            ("studying", ("etudier",)),
            ("playing", ("jouer",)),
            ("watching", ("regarder", "film", "anime")),
            ("listening", ("ecouter", "musique")),
        ):
            if any(word in text for word in words):
                availability = "unavailable" if activity == "sleeping" else "busy"
                return {"activity": activity, "availability": availability, "location": "outside"}
    if text in {"je travaille", "je bosse"} or text.startswith("je commence a travailler") or "je suis au travail" in text:
        return {"activity": "working", "availability": "busy"}
    if text in {"j etudie", "je revise", "je fais mes etudes"} or text.startswith("je commence a etudier"):
        return {"activity": "studying", "availability": "busy"}
    if text in {"je joue"} or text.startswith("je vais jouer") or text.startswith("je commence a jouer") or "je joue a un jeu" in text:
        return {"activity": "playing", "availability": "busy"}
    if any(phrase in text for phrase in ("je regarde un film", "je regarde un anime", "je regarde un anime", "je vais regarder un film", "je vais regarder un anime", "je commence un film", "je commence un anime")):
        return {"activity": "watching", "availability": "busy"}
    if any(phrase in text for phrase in ("j ecoute de la musique", "je vais ecouter de la musique", "je mets de la musique", "je commence a ecouter de la musique")):
        return {"activity": "listening", "availability": "busy"}
    for activity, phrases in _ACTIVITY_PATTERNS:
        if any(phrase in text for phrase in phrases):
            if activity == "home":
                return {"activity": "home", "location": "home", "availability": "available"}
            if activity == "awake":
                return {"activity": "awake", "availability": "available", "location": "home"}
            availability = "unavailable" if activity in {"sleeping", "outside"} else "busy"
            location = "outside" if activity == "outside" else None
            result = {"activity": activity, "availability": availability}
            if location:
                result["location"] = location
            return result

    if "je suis disponible" in text:
        return {"availability": "available"}
    if "je suis occupe" in text or "je suis occupé" in text:
        return {"availability": "busy"}
    return None


def detect_personal_state_question(message):
    text = _text(message)
    return any(marker in text for marker in _QUESTION_MARKERS) or (
        "je suis en train de manger" in text and str(message).strip().endswith("?")
    )


def update_personal_state(message, now=None):
    update = detect_personal_state(message)
    if not update:
        return None
    data = _load()
    state = data.setdefault("personal_state", {})
    state.update(update)
    state["started_at"] = (now or datetime.now().astimezone()).isoformat()
    data.setdefault("state_history", [])
    _save(data)
    if any(phrase in _text(message) for phrase in _FINISHED_EATING):
        return "D'accord. Je retiens que tu as fini de manger."
    if any(phrase in _text(message) for phrase in _FINISHED_WORKING):
        return "D'accord. Je retiens que tu as fini de travailler."
    if any(phrase in _text(message) for phrase in _FINISHED_STUDYING):
        return "D'accord. Je retiens que tu as fini d'étudier."
    if any(phrase in _text(message) for phrase in _FINISHED_PLAYING):
        return "D'accord. Je retiens que tu as fini de jouer."
    if any(phrase in _text(message) for phrase in _FINISHED_WATCHING):
        return "D'accord. Je retiens que tu as fini de regarder."
    if any(phrase in _text(message) for phrase in _FINISHED_LISTENING):
        return "D'accord. Je retiens que tu as fini d'écouter de la musique."
    activity = state.get("activity")
    labels = {
        "sleeping": "tu dors",
        "eating": "tu manges",
        "outside": "tu es dehors",
        "working": "tu travailles",
        "studying": "tu étudies",
        "gaming": "tu joues",
        "home": "tu es rentré",
        "awake": "tu es réveillé",
        "playing": "tu joues",
        "watching": "tu regardes un contenu",
        "listening": "tu écoutes de la musique",
    }
    if activity in labels:
        if activity == "eating":
            return "D'accord. Je retiens que tu vas manger."
        return f"D'accord. Je retiens que {labels[activity]}."
    if state.get("availability") == "available":
        return "D'accord. Je retiens que tu es disponible."
    return "D'accord. Je retiens que tu es occupé."


def get_personal_state():
    return dict(_load().get("personal_state", {}))


def _format_duration(started_at, now=None):
    try:
        started = datetime.fromisoformat(started_at)
        current = now or datetime.now(started.tzinfo)
        seconds = max(0, int((current - started).total_seconds()))
    except (TypeError, ValueError):
        return None
    minutes = seconds // 60
    if minutes < 1:
        return "moins d'une minute"
    hours, minutes = divmod(minutes, 60)
    parts = []
    if hours:
        parts.append(f"{hours} heure" + ("s" if hours > 1 else ""))
    if minutes:
        parts.append(f"{minutes} minute" + ("s" if minutes > 1 else ""))
    return " et ".join(parts)


def answer_personal_state_question(message, now=None):
    state = get_personal_state()
    if not state:
        return None
    text = _text(message)
    activity = state.get("activity")
    labels = {
        "sleeping": "Tu dors actuellement.",
        "eating": "Tu manges actuellement.",
        "outside": "Tu es actuellement dehors.",
        "working": "Tu travailles actuellement.",
        "studying": "Tu étudies actuellement.",
        "gaming": "Tu joues actuellement.",
        "home": "Tu es actuellement chez toi.",
    }
    if "est ce que je dors" in text or "dors depuis combien" in text or "depuis quand je dors" in text or "commence a dormir" in text:
        if activity != "sleeping":
            return "Tu ne dors pas actuellement."
        if "dors depuis combien" in text or "depuis combien" in text or "depuis quand je dors" in text:
            duration = _format_duration(state.get("started_at"), now=now)
            return f"Tu dors depuis environ {duration}." if duration else "Je n'ai pas l'heure de début de ton sommeil."
        return "Oui, tu dors actuellement."
    if "est ce que je mange" in text or "mange depuis combien" in text or "depuis quand je mange" in text or ("je suis en train de manger" in text and str(message).strip().endswith("?")):
        if activity != "eating":
            return "Tu ne manges pas actuellement."
        if "mange depuis combien" in text or "depuis quand je mange" in text:
            duration = _format_duration(state.get("started_at"), now=now)
            return f"Tu manges depuis environ {duration}." if duration else "Je n'ai pas l'heure de début de ton repas."
        return "Oui, tu manges actuellement."
    if "est ce que je travaille" in text or "travaille depuis combien" in text or "depuis combien de temps je travaille" in text or "depuis quand je travaille" in text or "commence a travailler" in text:
        if activity != "working":
            return "Tu ne travailles pas actuellement."
        if "depuis" in text or "commence a travailler" in text:
            duration = _format_duration(state.get("started_at"), now=now)
            return f"Tu travailles depuis environ {duration}." if duration else "Je n'ai pas l'heure de début de ton travail."
        return "Oui, tu travailles actuellement."
    if "est ce que j etudie" in text or "etudie depuis combien" in text or "depuis combien de temps j etudie" in text or "depuis quand j etudie" in text or "commence a etudier" in text:
        if activity != "studying":
            return "Tu n'étudies pas actuellement."
        if "depuis" in text or "commence a etudier" in text:
            duration = _format_duration(state.get("started_at"), now=now)
            return f"Tu étudies depuis environ {duration}." if duration else "Je n'ai pas l'heure de début de tes études."
        return "Oui, tu étudies actuellement."
    if "est ce que je joue" in text or "depuis combien de temps je joue" in text:
        if activity != "playing":
            return "Tu ne joues pas actuellement."
        if "depuis" in text:
            duration = _format_duration(state.get("started_at"), now=now)
            return f"Tu joues depuis environ {duration}." if duration else "Je n'ai pas l'heure de début de ton jeu."
        return "Oui, tu joues actuellement."
    if "est ce que je regarde" in text or "qu est ce que je regarde" in text or "depuis combien de temps je regarde" in text:
        if activity != "watching":
            return "Tu ne regardes rien actuellement."
        if "qu est ce que je regarde" in text:
            return "Tu regardes actuellement quelque chose."
        if "depuis" in text:
            duration = _format_duration(state.get("started_at"), now=now)
            return f"Tu regardes depuis environ {duration}." if duration else "Je n'ai pas l'heure de début de ce visionnage."
        return "Oui, tu regardes actuellement quelque chose."
    if "est ce que j ecoute" in text or "depuis combien de temps j ecoute" in text:
        if activity != "listening":
            return "Tu n'écoutes pas de musique actuellement."
        if "depuis" in text:
            duration = _format_duration(state.get("started_at"), now=now)
            return f"Tu écoutes de la musique depuis environ {duration}." if duration else "Je n'ai pas l'heure de début de cette écoute."
        return "Oui, tu écoutes actuellement de la musique."
    if "est ce que je suis dehors" in text or "ou suis je actuellement" in text or "depuis combien de temps je suis dehors" in text or "quand suis je sorti" in text:
        if state.get("location") != "outside":
            return "Tu n'es pas actuellement dehors."
        if "depuis combien de temps je suis dehors" in text or "quand suis je sorti" in text:
            duration = _format_duration(state.get("started_at"), now=now)
            return f"Tu es dehors depuis environ {duration}." if duration else "Je n'ai pas l'heure de début de ta sortie."
        return "Tu es actuellement dehors."
    if "est ce que je suis a la maison" in text:
        return "Oui, tu es actuellement à la maison." if state.get("location") == "home" else "Non, tu n'es pas actuellement à la maison."
    if "quel est mon etat actuel" in text:
        labels = {
            "sleeping": "Tu dors actuellement.", "awake": "Tu es réveillé actuellement.",
            "working": "Tu travailles actuellement.", "eating": "Tu manges actuellement.",
            "studying": "Tu étudies actuellement.", "gaming": "Tu joues actuellement.",
            "playing": "Tu joues actuellement.", "watching": "Tu regardes actuellement quelque chose.",
            "listening": "Tu écoutes actuellement de la musique.",
            "outside": "Tu es actuellement dehors.", "home": "Tu es actuellement chez toi.",
        }
        return labels.get(activity)
    if "disponible" in text:
        return "Oui, tu es actuellement disponible." if state.get("availability") == "available" else "Non, tu es actuellement occupé."
    if "ou suis je" in text:
        return "Tu es actuellement dehors." if state.get("location") == "outside" else "Tu es actuellement chez toi." if state.get("location") == "home" else None
    if "depuis quand" in text:
        started = state.get("started_at")
        if started:
            return f"Tu es dans cet état depuis {started}."
    return labels.get(activity)
