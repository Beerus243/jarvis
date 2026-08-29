from __future__ import annotations
import subprocess, time
from .command_registry import CommandDefinition
from .execution import ExecutionResult, ExecutionStatus

def run_command(command_definition: CommandDefinition, action_id: str='command') -> ExecutionResult:
    started=time.monotonic()
    try:
        result=subprocess.run([command_definition.executable,*command_definition.arguments], shell=False, capture_output=True, text=True, timeout=command_definition.timeout, cwd=command_definition.working_directory, check=False)
        status=ExecutionStatus.SUCCESS if result.returncode in command_definition.allowed_exit_codes else ExecutionStatus.FAILED
        return ExecutionResult(action_id,status,result.returncode,result.stdout,result.stderr,time.monotonic()-started)
    except subprocess.TimeoutExpired as exc: return ExecutionResult(action_id,ExecutionStatus.FAILED,duration=time.monotonic()-started,error=f'timeout: {exc}')
    except FileNotFoundError as exc: return ExecutionResult(action_id,ExecutionStatus.FAILED,duration=time.monotonic()-started,error=str(exc))
    except PermissionError as exc: return ExecutionResult(action_id,ExecutionStatus.FAILED,duration=time.monotonic()-started,error=str(exc))
    except (OSError, subprocess.SubprocessError) as exc: return ExecutionResult(action_id,ExecutionStatus.FAILED,duration=time.monotonic()-started,error=str(exc))
