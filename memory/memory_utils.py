"""Utilitaires de maintenance de la mémoire persistante."""

from collections.abc import MutableMapping


IMPORTANCE_RANK = {"basse": 1, "moyenne": 2, "haute": 3}


def _memory_key(souvenir):
    return " ".join(souvenir.get("contenu", "").casefold().split())


def clean_duplicate_memories(user: MutableMapping) -> int:
    """Supprime les doublons exacts et garde la meilleure occurrence.

    La meilleure occurrence est celle qui a l'importance la plus élevée,
    puis celle qui possède un embedding valide. Les IDs et embeddings de cette
    occurrence sont conservés tels quels.
    """

    souvenirs = user.get("souvenirs", [])
    best_by_key = {}
    order = []

    for souvenir in souvenirs:
        key = _memory_key(souvenir)
        if not key:
            continue
        if key not in best_by_key:
            order.append(key)
            best_by_key[key] = souvenir
            continue

        current = best_by_key[key]
        current_rank = IMPORTANCE_RANK.get(current.get("importance", ""), 0)
        candidate_rank = IMPORTANCE_RANK.get(souvenir.get("importance", ""), 0)
        current_has_embedding = bool(current.get("embedding"))
        candidate_has_embedding = bool(souvenir.get("embedding"))
        if (candidate_rank, candidate_has_embedding) > (
            current_rank,
            current_has_embedding,
        ):
            best_by_key[key] = souvenir

    cleaned = [best_by_key[key] for key in order]
    removed = len(souvenirs) - len(cleaned)
    user["souvenirs"] = cleaned
    return removed

