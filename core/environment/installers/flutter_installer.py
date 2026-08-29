from __future__ import annotations
from pathlib import Path
from ..execution import ExecutionResult, ExecutionStatus
from ..resolvers import FlutterEnvironmentResolver

class FlutterInstaller:
    """Safety-first installer facade; it never downloads or executes remote scripts."""
    def __init__(self, destination: str|Path|None=None):
        self.destination=Path(destination or Path.home()/'development/flutter').expanduser()
    def inspect(self) -> dict: return FlutterEnvironmentResolver().resolve()
    def install(self, *, confirmed: bool=False, network_available: bool=False) -> ExecutionResult:
        if self.inspect().get('flutter'): return ExecutionResult('flutter-install',ExecutionStatus.SKIPPED,error='Flutter est déjà installé.')
        if not confirmed: return ExecutionResult('flutter-install',ExecutionStatus.WAITING_CONFIRMATION,error='Confirmation requise.')
        if not network_available: return ExecutionResult('flutter-install',ExecutionStatus.BLOCKED,error='Réseau ou source contrôlée indisponible.')
        return ExecutionResult('flutter-install',ExecutionStatus.BLOCKED,error='Aucune méthode d’installation contrôlée configurée.')
