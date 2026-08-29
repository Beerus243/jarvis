from __future__ import annotations
from .actions import ActionType
from .command_registry import get_command
from .command_runner import run_command
from .execution import ExecutionResult, ExecutionStatus
from .execution_policy import evaluate_action, request_confirmation
from .execution_history import record_result
from .verification import verify_action
from .repair_executor import execute_repair

def execute_action(action, confirmation_handler=None, dry_run=False):
    policy, error=evaluate_action(action)
    if dry_run: return ExecutionResult(action.id, ExecutionStatus.SKIPPED, metadata={'dry_run':True})
    if policy == ExecutionStatus.BLOCKED: result=ExecutionResult(action.id, policy, error=error)
    elif policy == ExecutionStatus.WAITING_CONFIRMATION and not request_confirmation(action, confirmation_handler): result=ExecutionResult(action.id, policy, error='Confirmation refusée ou absente.')
    elif getattr(action.action_type,'value',action.action_type) != 'VERIFY': result=ExecutionResult(action.id, ExecutionStatus.BLOCKED, error='Cette action ne possède pas encore d\'exécuteur contrôlé.')
    elif getattr(action.action_type,'value',action.action_type) == 'CONFIGURE':
        result=execute_repair(action, confirmed=True)
    else:
        result=verify_action(action)
    record_result(result); return result

def execute_plan(plan, confirmation_handler=None, dry_run=False):
    results=[]; completed=set()
    for action in plan.actions:
        if any(dep not in completed for dep in action.dependencies):
            result=ExecutionResult(action.id,ExecutionStatus.SKIPPED,error='Dépendance non satisfaite.')
        else: result=execute_action(action, confirmation_handler, dry_run)
        results.append(result)
        if result.status == ExecutionStatus.SUCCESS or dry_run: completed.add(action.id)
        elif result.status in (ExecutionStatus.FAILED,ExecutionStatus.BLOCKED): break
    return results

def execute_plan_with_replan(plan, planner, inspector, confirmation_handler=None, dry_run=False, max_replans=2):
    """Execute a plan and re-inspect at most ``max_replans`` times after failure."""
    current=plan
    for attempt in range(max_replans+1):
        results=execute_plan(current, confirmation_handler, dry_run)
        if dry_run or not any(r.status in (ExecutionStatus.FAILED, ExecutionStatus.BLOCKED) for r in results): return results
        if attempt >= max_replans: return results
        current=planner(inspector())
    return results
