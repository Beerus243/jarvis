"""Short-lived, typed environment plan confirmation state."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid

TTL = timedelta(minutes=10)

@dataclass
class PendingEnvironmentPlan:
    plan_id: str
    intent: object
    created_at: datetime
    sensitive: bool = True

_pending: PendingEnvironmentPlan | None = None

def set_pending(intent):
    global _pending
    _pending = PendingEnvironmentPlan(f"ENV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}", intent, datetime.now(timezone.utc))
    return _pending

def get_pending():
    global _pending
    if _pending and datetime.now(timezone.utc) - _pending.created_at > TTL:
        _pending = None
    return _pending

def clear_pending():
    global _pending
    _pending = None
