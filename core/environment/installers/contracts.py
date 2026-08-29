from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from ..execution import ExecutionResult, ExecutionStatus

@dataclass(frozen=True)
class TrustedSource:
    provider: str; version: str; artifact_type: str; url: str|None = None; checksum: str|None = None; architecture: str|None = None
    def approved(self) -> bool: return bool(self.provider and self.version and self.url and self.url.startswith('https://'))

class EnvironmentInstaller:
    requirement=''
    def supports(self, requirement): return requirement == self.requirement
    def validate(self): return {'valid': False, 'reason': 'Installer non configuré.'}
    def plan(self): return []
    def install(self, **kwargs): return ExecutionResult('install', ExecutionStatus.BLOCKED, error='Installation bloquée : source fiable non configurée.')
    def verify(self): return self.validate()
