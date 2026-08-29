"""Typed, non-executable actions produced by the environment planner."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    INSTALL = "INSTALL"
    CONFIGURE = "CONFIGURE"
    VERIFY = "VERIFY"
    REPAIR = "REPAIR"
    SKIP = "SKIP"
    MANUAL = "MANUAL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKED = "BLOCKED"


@dataclass
class PlannedAction:
    id: str
    requirement: str
    action_type: ActionType | str
    description: str
    reason: str = ""
    dependencies: list[str] = field(default_factory=list)
    risk_level: RiskLevel | str = RiskLevel.LOW
    reversible: bool = True
    requires_confirmation: bool = False
    verification: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key in ("action_type", "risk_level"):
            value = result[key]
            result[key] = value.value if isinstance(value, Enum) else value
        return result


@dataclass
class ExecutionPlan:
    profile: str | None
    objective: str
    actions: list[PlannedAction] = field(default_factory=list)
    estimated_steps: int = 0
    requires_confirmation: bool = False
    blocked: bool = False
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.estimated_steps:
            self.estimated_steps = len(self.actions)
        self.requires_confirmation = self.requires_confirmation or any(
            action.requires_confirmation for action in self.actions
        )
        self.blocked = self.blocked or any(
            action.risk_level == RiskLevel.BLOCKED for action in self.actions
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "objective": self.objective,
            "actions": [action.to_dict() for action in self.actions],
            "estimated_steps": self.estimated_steps,
            "requires_confirmation": self.requires_confirmation,
            "blocked": self.blocked,
            "warnings": list(self.warnings),
        }
