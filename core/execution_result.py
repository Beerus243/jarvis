"""Résultat standardisé d'une exécution de source."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ExecutionResult:
    success: bool
    source: str
    response: Any = None
    error: Optional[str] = None
    fallback_allowed: bool = False
