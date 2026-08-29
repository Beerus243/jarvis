import subprocess
from .command_registry import get_command
from .execution import ExecutionResult, ExecutionStatus

def verify(name, executable=None, runner=subprocess.run):
    definition=get_command(name)
    if definition is None: return ExecutionResult(name,ExecutionStatus.BLOCKED,error='Commande non autorisée.')
    command=[executable or definition.executable,*definition.arguments]
    try:
        result=runner(command,capture_output=True,text=True,timeout=definition.timeout,check=False)
        status=ExecutionStatus.SUCCESS if result.returncode in definition.allowed_exit_codes else ExecutionStatus.FAILED
        return ExecutionResult(name,status,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr)
    except Exception as exc: return ExecutionResult(name,ExecutionStatus.FAILED,error=str(exc))
