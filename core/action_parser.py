"""Parseur déterministe des commandes d'action simples et composées."""

import re
from core.command_understanding import resolve_command_terms
from core.command_understanding import normalize_command


def _pc_action(text):
    """Parse les actions PC à paramètres structurés (sans commande shell)."""
    raw = str(text or "").strip()
    raw = re.sub(r"^(?:hey\s+)?jarvis\s*[, ]*", "", raw, flags=re.I)
    for pattern, kind in (
        (r"^(?:ouvre|ouvrir|open)\s+(?:moi\s+)?(?:le\s+)?fichier\s+[\"']?(.+?)[\"']?$", "FILE_OPEN"),
        (r"^(?:cree|crée)[- ]?(?:moi\s+)?un\s+fichier(?:\s+(?:au\s+nom\s+de|nomme|appele|appelé))?\s+[\"']?(.+?)[\"']?$", "FILE_CREATE"),
    ):
        match = re.match(pattern, raw, re.I)
        if match:
            return {"action": kind, "path": match.group(1).strip()}
    folder_raw = re.match(r"^(?:ouvre|ouvrir|open)\s+(?:moi\s+)?(?:le\s+)?dossier\s+[\"']?(.+?)[\"']?$", raw, re.I)
    if folder_raw:
        path = folder_raw.group(1).strip()
        return {"action": "OPEN_FOLDER", "path": path if ("/" in path or path.startswith("~")) else path.casefold()}
    if re.match(r"^(?:cree|crée)[- ]?(?:moi\s+)?un\s+fichier$", raw, re.I):
        return {"action": "FILE_CREATE", "needs_clarification": True}
    value = normalize_command(text)
    value = re.sub(r"^(?:hey\s+)?jarvis\s*[, ]*", "", value, flags=re.I)
    direct = {
        'quelles applications sont installees':'LIST_APPLICATIONS','quelles applications sont disponibles':'LIST_APPLICATIONS','liste les applications':'LIST_APPLICATIONS',
        'affiche mes fenetres':'WINDOW_LIST','liste les fenetres ouvertes':'WINDOW_LIST','quelle fenetre est active':'WINDOW_LIST','quelle application est active':'WINDOW_LIST',
        'active le wifi':'WIFI_ENABLE','active le wi fi':'WIFI_ENABLE','desactive le wifi':'WIFI_DISABLE','desactive le wi fi':'WIFI_DISABLE','quel est l etat du wifi':'WIFI_STATUS','quel est l etat du wi fi':'WIFI_STATUS',
        'active le bluetooth':'BLUETOOTH_ENABLE','desactive le bluetooth':'BLUETOOTH_DISABLE','le bluetooth est il active':'BLUETOOTH_STATUS',
        'quel est le volume':'VOLUME_STATUS','augmente la luminosite':'BRIGHTNESS_UP','baisse la luminosite':'BRIGHTNESS_DOWN',
        'ouvre les parametres':'WIFI_OPEN_SETTINGS', 'ouvre les parametres wifi':'WIFI_OPEN_SETTINGS',
        'ouvre les parametres bluetooth':'BLUETOOTH_OPEN_SETTINGS', 'ouvre les parametres audio':'WIFI_OPEN_SETTINGS',
    }
    if value in direct: return {'action': direct[value]}
    open_url = re.match(r"^(?:ouvre|ouvrir|lance|lancer|open|launch)\s+(?:moi\s+)?(youtube|google|github)$", value)
    if open_url:
        urls = {"youtube": "https://www.youtube.com", "google": "https://www.google.com", "github": "https://github.com"}
        return {"action": "OPEN_URL", "url": urls[open_url.group(1)]}
    folder = re.match(r"^(?:ouvre|ouvrir|open)\s+(?:moi\s+)?(?:le\s+)?dossier\s+(.+)$", value)
    if folder:
        return {"action": "OPEN_FOLDER", "path": folder.group(1).strip()}
    file_open = re.match(r"^(?:ouvre|ouvrir|open)\s+(?:moi\s+)?(?:le\s+)?fichier\s+(.+)$", value)
    if file_open:
        return {"action": "FILE_OPEN", "path": file_open.group(1).strip()}
    create = re.match(r"^(?:cree|crée)\s+(?:moi\s+)?un\s+fichier(?:\s+(?:au\s+nom\s+de|nomme|appele))?\s+(.+)$", value)
    if create:
        return {"action": "FILE_CREATE", "path": create.group(1).strip()}
    return None


def _one(text):
    value = text.strip()
    if (pc := _pc_action(value)):
        return pc
    low = resolve_command_terms(value)["normalized_terms"]

    # ============================================================
    # CONTRÔLE SPOTIFY — PAUSE
    # ============================================================

    if re.search(
        r"\ben\s+pause\b",
        low,
    ):
        return {"action": "PAUSE_MUSIC"}

    if re.search(
        r"\bpause\b",
        low,
    ) and re.search(
        r"\b(?:musique|spotify)\b",
        low,
    ):
        return {"action": "PAUSE_MUSIC"}

    # ============================================================
    # CONTRÔLE SPOTIFY — REPRISE
    # ============================================================

    if re.search(
        r"\b(?:reprends|reprend|reprise|continue)\b",
        low,
    ):
        if re.search(
            r"\b(?:musique|spotify|lecture)\b",
            low,
        ):
            return {"action": "RESUME_MUSIC"}

    # ============================================================
    # CONTRÔLE SPOTIFY — MORCEAU SUIVANT
    # ============================================================

    if re.search(
        r"\b(?:morceau|chanson|titre)\s+(?:suivant|suivante)\b",
        low,
    ):
        return {"action": "NEXT_TRACK"}

    # ============================================================
    # CONTRÔLE SPOTIFY — MORCEAU PRÉCÉDENT
    # ============================================================

    if re.search(
        r"\b(?:morceau|chanson|titre)\s+"
        r"(?:précédent|precedent|précédente|precedente)\b",
        low,
    ):
        return {"action": "PREVIOUS_TRACK"}

    # ============================================================
    # NAVIGATEUR
    # ============================================================

    if re.search(
        r"(?:ouvre|ouvrir|lance|lancer|demarre)\s+"
        r"(?:mon\s+)?"
        r"(?:browser|navigateur|chrome|google chrome)",
        low,
    ):
        return {"action": "OPEN_BROWSER"}

    # ============================================================
    # SPOTIFY
    # ============================================================

    if re.search(
        r"(?:open|ouvre|ouvrir|lance|lancer)\s+spotify",
        low,
    ):
        return {
            "action": "OPEN_APPLICATION",
            "target": "spotify",
        }

    # ============================================================
    # LECTURE MUSICALE
    # ============================================================

    if re.search(
        r"(?:play|joue|mets|met|lance)\s+",
        low,
    ):
        query = re.sub(
            r"^(?:play|joue|jouer|mets(?:[- ]moi)?|"
            r"met(?:[- ]moi)?|lance)\s+",
            "",
            low,
            flags=re.I,
        ).strip()

        query = re.sub(
            r"^(?:moi\s+)?du\s+",
            "",
            query,
        ).strip()
        query = re.sub(r"^moi\s+", "", query).strip()

        if query in {"", "une musique", "de la musique", "un morceau", "quelque chose"}:
            return {"action": "PLAY_MUSIC", "needs_clarification": True}

        request = {
            "action": "PLAY_MUSIC",
            "query": query,
        }

        known_artists = {
            "damso",
            "dadju",
            "booba",
            "nekfeu",
            "gims",
            "stromae",
        }

        words = query.split()

        if len(words) > 1 and words[0] in known_artists:
            artist, title = query.split(
                maxsplit=1
            )

            request.update(
                {
                    "title": title.strip(),
                    "artist": artist.strip(),
                }
            )

        elif " de " in query:
            title, artist = query.rsplit(
                " de ",
                1,
            )

            request.update(
                {
                    "title": title.strip(),
                    "artist": artist.strip(),
                }
            )

        elif query:
            request["artist"] = query

        return request

    # ============================================================
    # WIKIPÉDIA
    # ============================================================

    match = re.search(
        r"(?:search|cherche)\s+(.+?)\s+"
        r"(?:dans|sur)\s+(?:wikipedia|wiki)",
        low,
        re.I,
    )

    if match:
        return {
            "action": "SEARCH_WIKIPEDIA",
            "query": match.group(1).strip(),
        }

    match = re.search(
        r"(?:search|cherche|recherche|trouve|va chercher)\s+"
        r"(.+?)\s+(?:dans|sur)\s+(?:wikipedia|wiki)",
        low,
        re.I,
    )

    if match:
        return {
            "action": "SEARCH_WIKIPEDIA",
            "query": match.group(1).strip(),
        }

    # ============================================================
    # RECHERCHE INTERNET
    # ============================================================

    match = re.search(
        r"(?:search|cherche)\s+(.+?)\s+sur\s+internet",
        low,
        re.I,
    )

    if match:
        return {
            "action": "SEARCH_WEB",
            "query": match.group(1).strip(),
        }

    match = re.search(
        r"(?:search|cherche|recherche|trouve)\s+"
        r"(.+?)\s+(?:sur|dans)\s+"
        r"(?:chrome|firefox|browser|navigateur)",
        low,
        re.I,
    )

    if match:
        return {
            "action": "SEARCH_WEB",
            "query": match.group(1).strip(),
        }

    match = re.search(
        r"(?:search|cherche|recherche|trouve)\s+(.+)",
        low,
        re.I,
    )

    if match:
        return {
            "action": "SEARCH_WEB",
            "query": match.group(1).strip(),
        }

    # ============================================================
    # OUVERTURE WIKIPÉDIA
    # ============================================================

    if re.search(
        r"(?:va|ouvre)\s+(?:sur\s+)?(?:wikipedia|wiki)",
        low,
    ):
        return {
            "action": "OPEN_URL",
            "url": "https://fr.wikipedia.org",
        }

    # ============================================================
    # YOUTUBE
    # ============================================================

    if re.search(
        r"ouvre\s+youtube",
        low,
    ):
        return {
            "action": "OPEN_URL",
            "url": "https://www.youtube.com",
        }

    # ============================================================
    # FALLBACK WIKIPÉDIA
    # ============================================================

    if (
        "open" in low
        or "ouvre" in low
    ) and "wikipedia" in low:
        return {
            "action": "OPEN_URL",
            "url": "https://fr.wikipedia.org",
        }

    return None


def parse_actions(message):
    raw = str(message or "")

    # Autorise :
    # "ouvre Spotify met Damso"
    # sans exiger le mot "et".
    raw = re.sub(
        r"((?:ouvre|lance)\s+(?:spotify))\s+"
        r"(?=(?:met|mets|joue)\b)",
        r"\1 et ",
        raw,
        flags=re.I,
    )

    parts = [
        part
        for part in re.split(
            r"\s+(?:puis|et)\s+",
            raw,
            flags=re.I,
        )
        if part.strip()
    ]

    return [
        item
        for part in parts
        if (item := _one(part))
    ]
