import json

MEMORY_FILE = "user.json"


def clean_duplicates():

    with open(
        MEMORY_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        user = json.load(f)

    souvenirs = user.get(
        "souvenirs",
        []
    )

    vus = set()
    nouveaux = []

    for souvenir in souvenirs:

        contenu = souvenir.get(
            "contenu",
            ""
        ).strip().lower()

        if not contenu:
            continue

        if contenu in vus:

            print(
                "Doublon supprimé :",
                souvenir.get("contenu")
            )

            continue

        vus.add(contenu)

        nouveaux.append(
            souvenir
        )

    user["souvenirs"] = nouveaux

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            user,
            f,
            indent=4,
            ensure_ascii=False
        )

    print()
    print(
        "Souvenirs avant :",
        len(souvenirs)
    )

    print(
        "Souvenirs après :",
        len(nouveaux)
    )

    print()
    print("Nettoyage terminé.")


if __name__ == "__main__":

    clean_duplicates()