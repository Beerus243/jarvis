from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class PCAction:
    action_type: str
    parameters: dict[str, Any] | None = None

@dataclass(frozen=True)
class ActionResult:
    action_type: str
    success: bool
    message: str
    artifact_path: str | None = None
    error: str | None = None
