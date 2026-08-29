from .research import EnvironmentResearchRequest, EnvironmentResearcher
from .preparation import EnvironmentPreparationEngine
class EnvironmentPreparationService:
    def __init__(self, researcher=None, engine=None): self.researcher=researcher or EnvironmentResearcher(); self.engine=engine or EnvironmentPreparationEngine()
    def prepare(self, environment, *, dry_run=True, architecture='x86_64'):
        research=self.researcher.research(EnvironmentResearchRequest(environment, architecture=architecture))
        if research.status != 'READY': return {'status':'NEEDS_RESEARCH','research':research,'plan':None}
        return {'status':'PLANNED','research':research,'plan':self.engine.prepare(environment)}
