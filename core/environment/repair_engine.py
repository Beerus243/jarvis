from __future__ import annotations
from dataclasses import dataclass
from .execution import ExecutionResult, ExecutionStatus
from dataclasses import field

@dataclass(frozen=True)
class RepairDecision:
    available: bool
    action: str|None = None
    reason: str = ''

REPAIRABLE = {'javac':'CONFIGURE javac', 'adb':'CONFIGURE adb', 'flutter':'VERIFY flutter', 'dart':'VERIFY dart'}

@dataclass(frozen=True)
class RepairOperation:
    action: str; reason: str=''; requires_confirmation: bool=True

@dataclass
class RepairReport:
    results: list[ExecutionResult] = field(default_factory=list)
    def to_dict(self): return {'results':[r.to_dict() for r in self.results], 'success':bool(self.results) and all(r.status==ExecutionStatus.SUCCESS for r in self.results)}

class RepairEngine:
    ALLOWED={'CONFIGURE_PATH','CONFIGURE_ENVIRONMENT','INSTALL_JDK','INSTALL_ANDROID_COMPONENT','ACCEPT_ANDROID_LICENSES','VERIFY','VERIFY_TOOLCHAIN','REPAIR'}
    def __init__(self, handlers=None): self.handlers=handlers or {}
    def execute(self, plan, *, dry_run=True, confirmation_handler=None):
        results=[]
        for operation in plan.actions:
            if operation.action not in self.ALLOWED:
                results.append(ExecutionResult(operation.action,ExecutionStatus.BLOCKED,error='Opération de réparation inconnue.')); break
            if dry_run:
                results.append(ExecutionResult(operation.action,ExecutionStatus.SKIPPED,metadata={'dry_run':True})); continue
            if operation.requires_confirmation and not (confirmation_handler and confirmation_handler(operation)):
                results.append(ExecutionResult(operation.action,ExecutionStatus.CANCELLED,error='Confirmation refusée ou absente.')); break
            handler=self.handlers.get(operation.action)
            if handler is None:
                results.append(ExecutionResult(operation.action,ExecutionStatus.BLOCKED,error='Opération non configurée.')); break
            try:
                value=handler(operation); result=value if isinstance(value,ExecutionResult) else ExecutionResult(operation.action,ExecutionStatus.SUCCESS)
            except Exception as exc: result=ExecutionResult(operation.action,ExecutionStatus.FAILED,error=str(exc))
            results.append(result)
            if result.status != ExecutionStatus.SUCCESS: break
        return RepairReport(results)

def diagnose_failure(result: ExecutionResult, requirement: str|None = None) -> RepairDecision:
    if result.status not in (ExecutionStatus.FAILED, ExecutionStatus.BLOCKED):
        return RepairDecision(False, reason='Aucun échec à réparer.')
    if requirement in REPAIRABLE:
        return RepairDecision(True, REPAIRABLE[requirement], 'Une stratégie de réparation contrôlée existe.')
    return RepairDecision(False, reason='Aucune réparation sûre déclarée.')

def run_with_replan(plan, *, execute, inspect, resolve_and_plan, max_replans=2):
    """Execute/reinspect/replan with a hard retry bound (never an infinite loop)."""
    results=[]; current=plan
    for attempt in range(max(0, max_replans)+1):
        results=execute(current)
        failed=next((r for r in results if r.status in (ExecutionStatus.FAILED, ExecutionStatus.BLOCKED)), None)
        if failed is None: return results
        if attempt >= max_replans: return results
        current=resolve_and_plan(inspect())
    return results
