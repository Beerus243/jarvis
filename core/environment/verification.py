from __future__ import annotations
from .actions import PlannedAction
from .command_registry import get_command
from .command_runner import run_command
from .execution import ExecutionResult, ExecutionStatus

COMMANDS = {'git':'verify_git','python':'verify_python','java':'verify_java','javac':'verify_javac',
            'adb':'verify_adb','flutter':'verify_flutter','dart':'verify_dart',
            'android_toolchain':'verify_android_toolchain'}

def verify_action(action: PlannedAction) -> ExecutionResult:
    key=COMMANDS.get(action.requirement)
    definition=get_command(key) if key else None
    if definition is None:
        return ExecutionResult(action.id, ExecutionStatus.BLOCKED, error='Vérification non déclarée dans le registre.', verification_status='UNKNOWN')
    result=run_command(definition, action.id)
    result.verification_status='SUCCESS' if result.status == ExecutionStatus.SUCCESS else 'FAILED'
    return result
