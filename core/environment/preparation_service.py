from .research import EnvironmentResearchRequest, EnvironmentResearcher
from .preparation import EnvironmentPreparationEngine
from .local_artifacts import LocalArtifactDiscovery
from .local_sdks import LocalSDKDiscovery
from .android_sdk import AndroidSDKDiscovery
from pathlib import Path
class EnvironmentPreparationService:
    def __init__(self, researcher=None, engine=None, local_discovery=None, sdk_discovery=None): self.researcher=researcher or EnvironmentResearcher(); self.engine=engine or EnvironmentPreparationEngine(); self.local_discovery=local_discovery or LocalArtifactDiscovery(); self.sdk_discovery=sdk_discovery or LocalSDKDiscovery()
    def prepare(self, environment, *, dry_run=True, architecture='x86_64'):
        if str(environment).lower() == 'flutter':
            sdks=self.sdk_discovery.discover(architecture=architecture)
            if sdks:
                sdk=sdks[0]
                toolchain=AndroidSDKDiscovery().discover()
                if sdk.state=='READY': return {'status':'ALREADY_READY','source':'LOCAL_SDK','sdk':sdk,'toolchain':toolchain,'research':None,'plan':None}
                from .installers.flutter_installer import FlutterInstaller
                toolchain=AndroidSDKDiscovery().discover()
                return {'status':'SDK_PRESENT','source':'LOCAL_SDK','sdk':sdk,'toolchain':toolchain,'research':None,'plan':FlutterInstaller().plan_existing()}
            local=self.local_discovery.discover(architecture=architecture)
            if local:
                artifact=self.local_discovery.to_installation_artifact(local[0], Path.home()/'.local/share/jarvis/environments/flutter'/ (local[0].version or 'unknown'))
                if artifact:
                    return {'status':'PLANNED','source':'LOCAL_ARTIFACT','candidate':local[0],'artifact':artifact,'research':None,'plan':self.engine.prepare(environment)}
        research=self.researcher.research(EnvironmentResearchRequest(environment, architecture=architecture))
        if research.status != 'READY': return {'status':'NEEDS_RESEARCH','research':research,'plan':None}
        return {'status':'PLANNED','research':research,'plan':self.engine.prepare(environment)}
