"""Propositions locales déclenchées par le contexte personnel et PC."""

from datetime import datetime

_seen = {}


def detect_pc_proposals(personal_context, pc_context, now=None, cooldown_minutes=30):
    personal_context = personal_context or {}
    pc_context = pc_context or {}
    current = now or datetime.now().astimezone()
    proposals = []
    battery = (pc_context.get("battery") or {})
    if battery.get("level") is not None and battery.get("level") < 20 and not battery.get("charging"):
        key = "low_battery"
        previous = _seen.get(key)
        if not previous or (current - previous).total_seconds() >= cooldown_minutes * 60:
            _seen[key] = current
            proposals.append({"type": key, "reason": "Ta batterie est faible. Veux-tu brancher ton PC ?", "priority": "high", "created_at": current.isoformat()})
    return proposals


def clear_pc_proposals():
    _seen.clear()
