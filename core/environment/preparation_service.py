from .research import EnvironmentResearchRequest, EnvironmentResearcher
from .preparation import EnvironmentPreparationEngine
from .local_artifacts import LocalArtifactDiscovery
from pathlib import Path
class EnvironmentPreparationService:
    def __init__(self, researcher=None, engine=None, local_discovery=None): self.researcher=researcher or EnvironmentResearcher(); self.engine=engine or EnvironmentPreparationEngine(); self.local_discovery=local_discovery or LocalArtifactDiscovery()
    def prepare(self, environment, *, dry_run=True, architecture='x86_64'):
        if str(environment).lower() == 'flutter':
            local=self.local_discovery.discover(architecture=architecture)
            if local:
                artifact=self.local_discovery.to_installation_artifact(local[0], Path.home()/'.local/share/jarvis/environments/flutter'/ (local[0].version or 'unknown'))
                if artifact:
                    return {'status':'PLANNED','source':'LOCAL_ARTIFACT','candidate':local[0],'artifact':artifact,'research':None,'plan':self.engine.prepare(environment)}
        research=self.researcher.research(EnvironmentResearchRequest(environment, architecture=architecture))
        if research.status != 'READY': return {'status':'NEEDS_RESEARCH','research':research,'plan':None}
        return {'status':'PLANNED','research':research,'plan':self.engine.prepare(environment)}
