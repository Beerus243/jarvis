"""Prépare une réponse texte pour une lecture naturelle."""

import re


def format_for_speech(text):
    if not text:
        return ""

    value = str(text).strip()
    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::\d{2})?", value)
    if match:
        hour, minute = (int(part) for part in match.groups())
        return f"{hour} heure" + ("s" if hour != 1 else "") + (
            f" {minute} minute" + ("s" if minute != 1 else "")
            if minute else ""
        )
    return value
