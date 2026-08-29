from .contracts import EnvironmentInstaller
from .artifacts import InstallationPlan, InstallationStep
class NodeInstaller(EnvironmentInstaller):
    requirement='node'
    def plan(self): return InstallationPlan('node',[InstallationStep('node-verify','node','VERIFY',1,[],risk_level='LOW',requires_confirmation=False),InstallationStep('npm-verify','npm','VERIFY',2,['node-verify'],risk_level='LOW',requires_confirmation=False)])
