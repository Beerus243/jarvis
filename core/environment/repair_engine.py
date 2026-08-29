from __future__ import annotations
from dataclasses import dataclass
from .execution import ExecutionResult, ExecutionStatus

@dataclass(frozen=True)
class RepairDecision:
    available: bool
    action: str|None = None
    reason: str = ''

REPAIRABLE = {'javac':'CONFIGURE javac', 'adb':'CONFIGURE adb', 'flutter':'VERIFY flutter', 'dart':'VERIFY dart'}

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
