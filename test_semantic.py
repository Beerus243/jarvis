from memory import search_memory


# ============================================================
# TEST DE RECHERCHE SÉMANTIQUE
# ============================================================

query = "Sur quoi est-ce que je travaille actuellement ?"


results = search_memory(
    query
)


print()
print("========================================")
print("      RECHERCHE SÉMANTIQUE")
print("========================================")


for result in results:

    souvenir = result["souvenir"]
    score = result["score"]

    print()
    print(f"Score : {score:.4f}")
    print(
        f"Souvenir : "
        f"{souvenir.get('contenu')}"
    )
    print(
        f"Catégorie : "
        f"{souvenir.get('categorie')}"
    )