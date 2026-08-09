import json


def get_context():

    with open("user.json", "r") as f:
        user = json.load(f)

    identite = user.get("identite", {})
    preferences = user.get("preferences", {})
    memory = user.get("memory", {})
    habits = user.get("habits", {})

    context = f"""
Nom : {identite.get('name', 'inconnu')}
Postnom : {identite.get('postnom', '')}
Ville : {identite.get('ville', 'inconnue')}
Passions : {identite.get('passion', 'inconnues')}

Couleur préférée : {preferences.get('couleur', 'inconnue')}
Musique préférée : {preferences.get('musique', 'inconnue')}

Mémoire :
{memory}

Habitudes :
{habits}
"""

    return context