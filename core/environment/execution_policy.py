from .actions import ActionType, RiskLevel, PlannedAction
from .execution import ExecutionStatus

def evaluate_action(action: PlannedAction) -> tuple[ExecutionStatus, str|None]:
    risk=getattr(action.risk_level,'value',action.risk_level)
    typ=getattr(action.action_type,'value',action.action_type)
    if risk in ('HIGH','BLOCKED') or typ == 'MANUAL': return ExecutionStatus.BLOCKED, 'Action interdite ou nécessitant une intervention manuelle.'
    if typ in ('INSTALL','CONFIGURE','REPAIR') and action.requires_confirmation: return ExecutionStatus.WAITING_CONFIRMATION, None
    return ExecutionStatus.PENDING, None

def request_confirmation(action, handler=None) -> bool:
    if handler is not None: return bool(handler(action))
    return False
