"""Parseur déterministe des commandes d'action simples et composées."""

import re


def _one(text):
    value = text.strip()
    low = value.casefold()
    if re.search(r"(?:ouvre|lance|d[ée]marre)\s+(?:mon\s+)?(?:navigateur|chrome|google chrome)", low):
        return {"action": "OPEN_BROWSER"}
    if re.search(r"(?:ouvre|lance)\s+(?:spotify)", low):
        return {"action": "OPEN_APPLICATION", "target": "spotify"}
    if re.search(r"(?:joue|mets(?:-moi)?|lance)\s+", low):
        query = re.sub(r"^(?:joue|mets(?:-moi)?|lance)\s+", "", value, flags=re.I).strip()
        return {"action": "PLAY_MUSIC", "query": query}
    match = re.search(r"cherche\s+(.+?)\s+dans\s+(?:wikipedia|wikip[eé]dia)", value, re.I)
    if match:
        return {"action": "SEARCH_WIKIPEDIA", "query": match.group(1).strip()}
    match = re.search(r"cherche\s+(.+?)\s+sur\s+internet", value, re.I)
    if match:
        return {"action": "SEARCH_WEB", "query": match.group(1).strip()}
    if "ouvre" in low and "wikipedia" in low:
        return {"action": "OPEN_URL", "url": "https://fr.wikipedia.org"}
    return None


def parse_actions(message):
    parts = [p for p in re.split(r"\s+(?:puis|et)\s+", str(message or ""), flags=re.I) if p.strip()]
    actions = [item for part in parts if (item := _one(part))]
    return actions
