from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from .execution import ExecutionResult, ExecutionStatus

class InstallationState(str, Enum):
    NOT_STARTED='NOT_STARTED'; PLANNED='PLANNED'; WAITING_CONFIRMATION='WAITING_CONFIRMATION'; RUNNING='RUNNING'; VERIFYING='VERIFYING'; SUCCEEDED='SUCCEEDED'; FAILED='FAILED'; BLOCKED='BLOCKED'; SKIPPED='SKIPPED'; CANCELLED='CANCELLED'

@dataclass
class InstallationReport:
    results:list[ExecutionResult]=field(default_factory=list)
    def to_dict(self): return {'results':[r.to_dict() for r in self.results], 'success':bool(self.results) and all(r.status==ExecutionStatus.SUCCESS for r in self.results)}

def execute_installation_plan(plan, *, confirmation_handler=None, dry_run=True, operations=None):
    """Execute only typed installation steps. Real side effects require injected operations."""
    operations=operations or {}
    results=[]; done=set()
    for step in plan.steps:
        if any(dep not in done for dep in step.dependencies):
            results.append(ExecutionResult(step.id,ExecutionStatus.SKIPPED,error='Dépendance non satisfaite.')); break
        if dry_run:
            results.append(ExecutionResult(step.id,ExecutionStatus.SKIPPED,metadata={'dry_run':True})); done.add(step.id); continue
        if step.requires_confirmation and not (confirmation_handler and confirmation_handler(step)):
            results.append(ExecutionResult(step.id,ExecutionStatus.CANCELLED,error='Confirmation refusée ou absente.')); break
        operation=operations.get(step.action_type)
        if operation is None:
            results.append(ExecutionResult(step.id,ExecutionStatus.BLOCKED,error=f'Opération {step.action_type} non configurée.')); break
        started=monotonic()
        try: value=operation(step)
        except Exception as exc: results.append(ExecutionResult(step.id,ExecutionStatus.FAILED,duration=monotonic()-started,error=str(exc))); break
        result=value if isinstance(value,ExecutionResult) else ExecutionResult(step.id,ExecutionStatus.SUCCESS,duration=monotonic()-started)
        results.append(result)
        if result.status != ExecutionStatus.SUCCESS: break
        done.add(step.id)
    return InstallationReport(results)
