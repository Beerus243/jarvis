from __future__ import annotations
from dataclasses import dataclass, field
from .actions import RiskLevel

@dataclass(frozen=True)
class CommandDefinition:
    name: str; executable: str; arguments: tuple[str,...]=(); allowed_exit_codes: tuple[int,...]=(0,)
    timeout: float=10.0; risk_level: RiskLevel=RiskLevel.LOW; requires_confirmation: bool=False
    allowed_environment: tuple[str,...]=(); working_directory: str|None=None; requires_sudo: bool=False

COMMAND_REGISTRY = {
 'verify_git': CommandDefinition('verify_git','git',('--version',)),
 'verify_python': CommandDefinition('verify_python','python',('--version',)),
 'verify_java': CommandDefinition('verify_java','java',('--version',)),
 'verify_javac': CommandDefinition('verify_javac','javac',('--version',)),
 'verify_adb': CommandDefinition('verify_adb','adb',('version',)),
 'verify_flutter': CommandDefinition('verify_flutter','flutter',('--version',)),
 'verify_dart': CommandDefinition('verify_dart','dart',('--version',)),
 'verify_android_toolchain': CommandDefinition('verify_android_toolchain','flutter',('doctor',)),
}

def get_command(name: str) -> CommandDefinition | None: return COMMAND_REGISTRY.get(name)
