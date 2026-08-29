from .contracts import EnvironmentInstaller
from .artifacts import InstallationPlan, InstallationStep
class JdkInstaller(EnvironmentInstaller):
    requirement='java'
    def plan(self): return InstallationPlan('java',[InstallationStep('java-verify','java','VERIFY',1,[],risk_level='LOW',requires_confirmation=False),InstallationStep('javac-verify','javac','VERIFY',2,['java-verify'],risk_level='LOW',requires_confirmation=False)])
