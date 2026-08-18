"""Nettoie les doublons exacts de data/user.json."""

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import MEMORY_FILE
from memory.memory import load_memory, save_memory
from memory.memory_utils import clean_duplicate_memories


def clean_duplicates():
    user = load_memory()
    before = len(user.get("souvenirs", []))
    removed = clean_duplicate_memories(user)
    if removed:
        save_memory(user)
    print(f"Souvenirs avant : {before}")
    print(f"Doublons supprimés : {removed}")
    print(f"Souvenirs après : {len(user.get('souvenirs', []))}")
    return removed


if __name__ == "__main__":
    clean_duplicates()
