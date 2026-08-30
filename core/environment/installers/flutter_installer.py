from __future__ import annotations
from pathlib import Path
from ..execution import ExecutionResult, ExecutionStatus
from ..resolvers import FlutterEnvironmentResolver
from .contracts import EnvironmentInstaller, TrustedSource
from .artifacts import InstallationPlan, InstallationStep
from .artifacts import InstallationArtifact
from .contracts import TrustedSource

class FlutterInstaller(EnvironmentInstaller):
    """Safety-first installer facade; it never downloads or executes remote scripts."""
    def __init__(self, destination: str|Path|None=None):
        self.requirement='flutter'
        self.destination=Path(destination or Path.home()/'development/flutter').expanduser()
    def inspect(self) -> dict: return FlutterEnvironmentResolver().resolve()
    def inspect_installation(self, version=None):
        root=self.destination
        if version:
            root=root/version
        flutter=root/'flutter/bin/flutter'
        if flutter.exists() and (root/'flutter/bin/dart').exists(): return {'status':'READY','path':str(root),'version':version}
        if root.exists(): return {'status':'PARTIAL','path':str(root)}
        return {'status':'ABSENT','path':str(root)}
    def installation_status(self, version):
        return self.inspect_installation(version)['status']
    def artifact_from_research(self, research):
        if not research or research.status != 'READY' or not research.artifacts: return None
        item=research.artifacts[0]
        source=TrustedSource('Flutter',item.version,item.artifact,item.download_url,item.checksum,item.architecture)
        artifact=InstallationArtifact(item.artifact,item.version,item.platform,item.architecture,source,
                                       Path(item.artifact).suffix.lstrip('.'),Path.home()/'.local/share/jarvis/environments/flutter'/item.version,
                                       item.checksum,tuple(c.evidence for c in research.verification.get('evidence',())))
        return artifact if artifact.validate() else None
    def plan(self):
        return InstallationPlan('flutter',[InstallationStep('flutter-download','flutter','DOWNLOAD',1,[],risk_level='MEDIUM'),InstallationStep('flutter-verify-file','flutter','VERIFY',2,['flutter-download'],risk_level='LOW',requires_confirmation=False),InstallationStep('flutter-extract','flutter','EXTRACT',3,['flutter-verify-file'],risk_level='MEDIUM',requires_confirmation=False),InstallationStep('flutter-install','flutter','INSTALL',4,['flutter-extract'],risk_level='MEDIUM',requires_confirmation=False),InstallationStep('flutter-path','flutter','CONFIGURE_PATH',5,['flutter-install'],risk_level='MEDIUM',requires_confirmation=False),InstallationStep('flutter-verify','flutter','VERIFY_FLUTTER',6,['flutter-path'],risk_level='LOW',requires_confirmation=False),InstallationStep('dart-verify','dart','VERIFY_DART',7,['flutter-verify'],risk_level='LOW',requires_confirmation=False)])
    def install(self, *, confirmed: bool=False, network_available: bool=False) -> ExecutionResult:
        if self.inspect().get('flutter'): return ExecutionResult('flutter-install',ExecutionStatus.SKIPPED,error='Flutter est déjà installé.')
        if not confirmed: return ExecutionResult('flutter-install',ExecutionStatus.WAITING_CONFIRMATION,error='Confirmation requise.')
        if not network_available: return ExecutionResult('flutter-install',ExecutionStatus.BLOCKED,error='Réseau ou source contrôlée indisponible.')
        return ExecutionResult('flutter-install',ExecutionStatus.BLOCKED,error='Aucune méthode d’installation contrôlée configurée.')
