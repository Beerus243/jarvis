from __future__ import annotations
from datetime import datetime, timezone
from .execution import ExecutionResult

_HISTORY: list[dict] = []
def record_result(result: ExecutionResult) -> None:
    _HISTORY.append({'timestamp': datetime.now(timezone.utc).isoformat(), **result.to_dict()})
def get_history() -> list[dict]: return list(_HISTORY)
def clear_history() -> None: _HISTORY.clear()
