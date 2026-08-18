def format_project_update(attribute, old_value, new_value):

    labels = {
        "langage": "le langage",
        "backend": "le backend",
        "frontend": "le frontend",
        "base_de_donnees": "la base de données",
        "type": "le type de projet",
    }

    label = labels.get(
        attribute,
        attribute
    )

    if old_value is None:

        return (
            f"J'ai enregistré que {label} "
            f"utilise {new_value}."
        )

    if old_value == new_value:

        return (
            f"Cette information est déjà enregistrée : "
            f"{new_value}."
        )

    return (
        f"J'ai mis à jour {label} : "
        f"{old_value} → {new_value}."
    )