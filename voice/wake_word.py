"""Détection textuelle locale du wake word, sans moteur matériel dédié."""

import re
import unicodedata


class WakeWordDetector:
    def detect(self, text):
        if not text:
            return False
        value = unicodedata.normalize("NFD", str(text).casefold())
        value = "".join(char for char in value if unicodedata.category(char) != "Mn")
        return bool(re.search(r"\bjarvis\b", value))
