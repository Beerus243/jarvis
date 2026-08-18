import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory import remember


remember(
    "Le backend du projet JARVIS utilise FastAPI.",
    "projet",
    "haute"
)

remember(
    "Le projet JARVIS est développé principalement en Python.",
    "projet",
    "haute"
)

remember(
    "Le frontend de JARVIS utilise React.",
    "projet",
    "haute"
)

remember(
    "J'utilise PostgreSQL pour stocker les données du projet JARVIS.",
    "projet",
    "haute"
)

remember(
    "Le projet JARVIS utilise des embeddings pour sa mémoire sémantique.",
    "projet",
    "haute"
)

print("Souvenirs techniques ajoutés.")
