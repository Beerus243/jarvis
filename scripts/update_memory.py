import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory import update_missing_embeddings


print("Mise à jour de la mémoire...")

result = update_missing_embeddings()

if result:

    print("Embeddings ajoutés aux souvenirs.")

else:

    print("Aucune mise à jour nécessaire.")
