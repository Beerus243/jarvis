from pathlib import Path
from .execution import ExecutionResult, ExecutionStatus
from .resolvers import JavaEnvironmentResolver, AndroidEnvironmentResolver
from .user_path import prepare_path_update, apply_user_path_update
def execute_repair(action, *, confirmed=False):
    if not confirmed: return ExecutionResult(action.id, ExecutionStatus.WAITING_CONFIRMATION, error='Confirmation requise.')
    info = JavaEnvironmentResolver().resolve() if action.requirement == 'javac' else AndroidEnvironmentResolver().resolve() if action.requirement == 'adb' else None
    value = info.get(action.requirement) if info else None
    if not value: return ExecutionResult(action.id, ExecutionStatus.BLOCKED, error=f'Aucun {action.requirement} existant trouvé.')
    try: update=prepare_path_update(Path(value).expanduser().resolve().parent); ok=apply_user_path_update(update, confirmed=True)
    except (OSError, ValueError) as exc: return ExecutionResult(action.id, ExecutionStatus.FAILED, error=str(exc))
    return ExecutionResult(action.id, ExecutionStatus.SUCCESS if ok else ExecutionStatus.FAILED, metadata={'variable':update['variable'],'directory':update['directory']})
