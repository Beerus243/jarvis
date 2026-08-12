import unicodedata


CORRECTIONS = {
    "develloper": "developper",
    "develloppe": "developpe",
    "devellopé": "developpe",
    "dévelloper": "développer",
    "dévellopé": "développé",
    "developper": "développer",
    "developpe": "développe",
}


def normalize_text(text):

    text = text.lower().strip()

    for erreur, correction in CORRECTIONS.items():

        text = text.replace(
            erreur,
            correction
        )

    return text