from __future__ import annotations
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
import re

class ExecutionStatus(str, Enum):
    PENDING='PENDING'; WAITING_CONFIRMATION='WAITING_CONFIRMATION'; RUNNING='RUNNING'; SUCCESS='SUCCESS'; FAILED='FAILED'; SKIPPED='SKIPPED'; BLOCKED='BLOCKED'; CANCELLED='CANCELLED'

def sanitize_output(value: str | None) -> str:
    text = value or ''
    return re.sub(r'(?i)(api[_ -]?key|token|password|secret)(\s*[:=]\s*)\S+', r'\1\2[REDACTED]', text)

@dataclass
class ExecutionResult:
    action_id: str
    status: ExecutionStatus | str
    exit_code: int | None = None
    stdout: str = ''
    stderr: str = ''
    duration: float = 0.0
    error: str | None = None
    verification_status: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self):
        data=asdict(self); data['status']=self.status.value if isinstance(self.status,Enum) else self.status
        data['stdout']=sanitize_output(data['stdout']); data['stderr']=sanitize_output(data['stderr']); return data
