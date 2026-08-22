"""Détection locale de propositions proactives non dangereuses."""

from datetime import datetime


_last_proposals = {}


def detect_proposals(context, now=None, cooldown_minutes=30):
    context = context or {}
    activity = context.get("activity")
    started = context.get("started_at")
    if not activity or not started:
        return []
    try:
        begin = datetime.fromisoformat(started)
        current = now or datetime.now(begin.tzinfo)
        elapsed = (current - begin).total_seconds() / 60
    except (TypeError, ValueError):
        return []
    thresholds = {"sleeping": 480, "working": 120, "studying": 120}
    if activity not in thresholds or elapsed < thresholds[activity]:
        return []
    key = activity
    last = _last_proposals.get(key)
    if last and (current - last).total_seconds() < cooldown_minutes * 60:
        return []
    _last_proposals[key] = current
    messages = {
        "sleeping": "Tu dors depuis longtemps. Tu veux te réveiller ?",
        "working": "Tu travailles depuis 2 heures. Tu veux faire une pause ?",
        "studying": "Tu étudies depuis 2 heures. Tu veux faire une pause ?",
    }
    return [{"type": f"{activity}_reminder", "reason": messages[activity], "priority": "normal", "created_at": current.isoformat()}]


def clear_proposals():
    _last_proposals.clear()
