"""Parseur déterministe des commandes d'action simples et composées."""

import re
from core.command_understanding import resolve_command_terms


def _one(text):
    value = text.strip()
    low = resolve_command_terms(value)["normalized_terms"]
    if re.search(r"(?:ouvre|ouvrir|lance|lancer|demarre)\s+(?:mon\s+)?(?:browser|navigateur|chrome|google chrome)", low):
        return {"action": "OPEN_BROWSER"}
    if re.search(r"(?:open|ouvre|ouvrir|lance|lancer)\s+(?:spotify)", low):
        return {"action": "OPEN_APPLICATION", "target": "spotify"}
    if re.search(r"(?:play|joue|mets|met|lance)\s+", low):
        query = re.sub(r"^(?:play|joue|jouer|mets(?:[- ]moi)?|met(?:[- ]moi)?|lance)\s+", "", low, flags=re.I).strip()
        query = re.sub(r"^(?:moi\s+)?du\s+", "", query).strip()
        request = {"action": "PLAY_MUSIC", "query": query}
        if " de " in query:
            title, artist = query.rsplit(" de ", 1)
            request.update({"title": title.strip(), "artist": artist.strip()})
        elif query:
            request["artist"] = query
        return request
    match = re.search(r"(?:search|cherche)\s+(.+?)\s+(?:dans|sur)\s+(?:wikipedia|wiki)", low, re.I)
    if match:
        return {"action": "SEARCH_WIKIPEDIA", "query": match.group(1).strip()}
    match = re.search(r"(?:search|cherche|recherche|trouve|va chercher)\s+(.+?)\s+(?:dans|sur)\s+(?:wikipedia|wiki)", low, re.I)
    if match:
        return {"action": "SEARCH_WIKIPEDIA", "query": match.group(1).strip()}
    match = re.search(r"(?:search|cherche)\s+(.+?)\s+sur\s+internet", low, re.I)
    if match:
        return {"action": "SEARCH_WEB", "query": match.group(1).strip()}
    match = re.search(r"(?:search|cherche|recherche|trouve)\s+(.+)", low, re.I)
    if match:
        return {"action": "SEARCH_WEB", "query": match.group(1).strip()}
    if re.search(r"(?:va|ouvre)\s+(?:sur\s+)?(?:wikipedia|wiki)", low):
        return {"action": "OPEN_URL", "url": "https://fr.wikipedia.org"}
    if re.search(r"ouvre\s+(?:youtube)", low):
        return {"action": "OPEN_URL", "url": "https://www.youtube.com"}
    if ("open" in low or "ouvre" in low) and "wikipedia" in low:
        return {"action": "OPEN_URL", "url": "https://fr.wikipedia.org"}
    return None


def parse_actions(message):
    parts = [p for p in re.split(r"\s+(?:puis|et)\s+", str(message or ""), flags=re.I) if p.strip()]
    actions = [item for part in parts if (item := _one(part))]
    return actions
