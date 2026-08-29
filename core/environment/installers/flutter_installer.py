from __future__ import annotations
from pathlib import Path
from ..execution import ExecutionResult, ExecutionStatus
from ..resolvers import FlutterEnvironmentResolver
from .contracts import EnvironmentInstaller, TrustedSource
from .artifacts import InstallationPlan, InstallationStep

class FlutterInstaller(EnvironmentInstaller):
    """Safety-first installer facade; it never downloads or executes remote scripts."""
    def __init__(self, destination: str|Path|None=None):
        self.requirement='flutter'
        self.destination=Path(destination or Path.home()/'development/flutter').expanduser()
    def inspect(self) -> dict: return FlutterEnvironmentResolver().resolve()
    def plan(self):
        return InstallationPlan('flutter',[InstallationStep('flutter-download','flutter','DOWNLOAD',1,[],risk_level='MEDIUM'),InstallationStep('flutter-verify','flutter','VERIFY',2,['flutter-download'],risk_level='LOW',requires_confirmation=False),InstallationStep('dart-verify','dart','VERIFY',3,['flutter-verify'],risk_level='LOW',requires_confirmation=False)])
    def install(self, *, confirmed: bool=False, network_available: bool=False) -> ExecutionResult:
        if self.inspect().get('flutter'): return ExecutionResult('flutter-install',ExecutionStatus.SKIPPED,error='Flutter est déjà installé.')
        if not confirmed: return ExecutionResult('flutter-install',ExecutionStatus.WAITING_CONFIRMATION,error='Confirmation requise.')
        if not network_available: return ExecutionResult('flutter-install',ExecutionStatus.BLOCKED,error='Réseau ou source contrôlée indisponible.')
        return ExecutionResult('flutter-install',ExecutionStatus.BLOCKED,error='Aucune méthode d’installation contrôlée configurée.')
