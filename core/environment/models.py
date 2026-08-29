from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class CheckStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    UNKNOWN = "UNKNOWN"
    MISCONFIGURED = "MISCONFIGURED"


@dataclass
class EnvironmentCheck:
    name: str
    status: CheckStatus | str
    version: str | None = None
    path: str | None = None
    command: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    @property
    def installed(self) -> bool:
        return self.status == CheckStatus.PRESENT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value if isinstance(self.status, CheckStatus) else self.status
        return value
