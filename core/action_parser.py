"""Parseur déterministe des commandes d'action simples et composées."""

import re
from core.command_understanding import resolve_command_terms


def _one(text):
    value = text.strip()
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