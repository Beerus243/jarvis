"""Planification bornée des actions composées."""

from dataclasses import dataclass, asdict
import re

from core.intent import detect_intent


@dataclass
class PlannedAction:
    action: str
    message: str = ""


def plan_actions(message):
    """Transforme une phrase en petites actions locales, sans les exécuter."""
    parts = [p.strip() for p in re.split(r"\s+(?:puis|et ensuite|ensuite)\s+", str(message or ""), flags=re.I) if p.strip()]
    actions = []
    for part in parts:
        intent = detect_intent(part)
        if intent:
            actions.append(PlannedAction(intent, part))
        elif re.search(r"(?:va|ouvre|aller).*(?:youtube|github|google|site)", part, re.I):
            actions.append(PlannedAction("OPEN_WEBSITE", part))
    return actions


def plan_dicts(message):
    return [asdict(item) for item in plan_actions(message)]
