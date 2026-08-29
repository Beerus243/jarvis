"""Generic models used by the read-only requirement resolver."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RequirementStatus(str, Enum):
    SATISFIED = "SATISFIED"
    MISSING = "MISSING"
    MISCONFIGURED = "MISCONFIGURED"
    UNKNOWN = "UNKNOWN"
    PARTIAL = "PARTIAL"


@dataclass
class Requirement:
    name: str
    description: str = ""
    status: RequirementStatus | str = RequirementStatus.UNKNOWN
    required: bool = True
    detected_value: Any = None
    recommendation: str | None = None
    depends_on: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def optional(self) -> bool:
        return not self.required

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value if isinstance(self.status, Enum) else self.status
        result["optional"] = not self.required
        return result


@dataclass
class RequirementSet:
    profile: str
    requirements: list[Requirement] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"profile": self.profile, "description": self.description,
                "requirements": [item.to_dict() for item in self.requirements]}


@dataclass
class RequirementPlan:
    request: str
    profile: str | None
    requirements: list[Requirement] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[Requirement] = field(default_factory=list)
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request,
            "profile": self.profile,
            "requirements": [item.to_dict() for item in self.requirements],
            "gaps": [item.to_dict() for item in self.gaps],
            "actions": self.actions,
            "message": self.message,
        }
