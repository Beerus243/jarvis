from .contracts import EnvironmentInstaller
from .artifacts import InstallationPlan, InstallationStep, InstallationArtifact
from .contracts import TrustedSource
from ..research import validate_metadata
from pathlib import Path
class JdkInstaller(EnvironmentInstaller):
    requirement='java'
    def plan(self): return InstallationPlan('java',[InstallationStep('java-verify','java','VERIFY',1,[],risk_level='LOW',requires_confirmation=False),InstallationStep('javac-verify','javac','VERIFY',2,['java-verify'],risk_level='LOW',requires_confirmation=False)])
    def plan_installation(self): return InstallationPlan('java',[InstallationStep('jdk-download','java','DOWNLOAD',1,[],risk_level='MEDIUM'),InstallationStep('jdk-verify-file','java','VERIFY',2,['jdk-download'],risk_level='LOW',requires_confirmation=False),InstallationStep('jdk-extract','java','EXTRACT',3,['jdk-verify-file'],risk_level='MEDIUM',requires_confirmation=False),InstallationStep('jdk-install','java','INSTALL',4,['jdk-extract'],risk_level='MEDIUM',requires_confirmation=False),InstallationStep('java-home','java','CONFIGURE_JAVA_HOME',5,['jdk-install'],risk_level='MEDIUM'),InstallationStep('java-path','java','CONFIGURE_PATH',6,['java-home'],risk_level='MEDIUM'),InstallationStep('java-verify','java','VERIFY_JAVA',7,['java-path'],risk_level='LOW',requires_confirmation=False),InstallationStep('javac-verify','javac','VERIFY_JAVAC',8,['java-verify'],risk_level='LOW',requires_confirmation=False)])
    def artifact_from_research(self,research):
        if not research or research.status!='READY' or not research.artifacts: return None
        item=research.artifacts[0]
        source_def=next((s for s in research.official_sources if s.name == 'Eclipse Adoptium'), None)
        if source_def is None or not item.checksum:
            return None
        valid, _ = validate_metadata(item, source_def, expected_architecture='x86_64')
        if not valid or item.platform != 'linux' or not item.download_url.startswith('https://'):
            return None
        source=TrustedSource('Eclipse Adoptium',item.version,item.artifact,item.download_url,item.checksum,item.architecture)
        artifact=InstallationArtifact(item.artifact,item.version,item.platform,item.architecture,source,item.artifact.split('.')[-1],Path.home()/'.local/share/jarvis/environments/jdk'/item.version,item.checksum)
        return artifact if artifact.validate() else None
