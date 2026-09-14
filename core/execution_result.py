"""Résultat standardisé d'une exécution de source."""

from dataclasses import dataclass, field
from typing import Any, Optional

NONE = "NONE"
NOT_FOUND = "NOT_FOUND"
AMBIGUOUS = "AMBIGUOUS"
DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
EXTERNAL_ERROR = "EXTERNAL_ERROR"
INTERNAL_ERROR = "INTERNAL_ERROR"
ERROR_TYPES = frozenset({
    NONE,
    NOT_FOUND,
    AMBIGUOUS,
    DEPENDENCY_ERROR,
    EXTERNAL_ERROR,
    INTERNAL_ERROR,
})


@dataclass
class ExecutionResult:
    success: bool
    source: str
    response: Any = None
    error: Optional[str] = None
    fallback_allowed: bool = False
    error_type: str = NONE
    evidence: dict = field(default_factory=dict)

    @property
    def status(self):
        if self.success:
            return "SUCCEEDED"
        if self.error_type == "CONFIRMATION_REQUIRED":
            return "WAITING_CONFIRMATION"
        return "FAILED"
class CommandResponse(str):
    """Réponse opérationnelle à conserver lors de la mise en forme du dialogue."""
