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
    # The full written response remains in history/logs; only its spoken form changes.
    value = re.sub(r"```[^\n`]*\n[\s\S]*?(?:```|$)",
                   "Un extrait de code est disponible dans la réponse écrite.", value)
    value = re.sub(r"\[([^]\n]+)\]\(https?://[^)\s]+\)", r"\1", value)
    value = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", value)
    value = re.sub(r"(?m)^\s*[-*+]\s+", "", value)
    value = re.sub(r"\*\*(.+?)\*\*", r"\1", value)
    value = re.sub(r"`([^`\n]+)`", r"\1", value)
    return value.strip()
