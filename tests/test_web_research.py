from core.environment.web_research import WebLLMResearchProvider
from core.environment.research import EnvironmentResearchRequest
class FakeWeb:
    def search(self,*a,**k): return []
def test_web_llm_provider_keeps_structured_boundary():
    p=WebLLMResearchProvider(FakeWeb(),lambda evidence,request:{'version':'1','confidence':.9,'evidence_urls':['https://nodejs.org/dist/index.json']})
    result=p.research(EnvironmentResearchRequest('Node.js'))
    assert result.status=='READY' and result.verification['evidence'][0].value=='1'

def test_provider_rejects_untrusted_evidence():
    p=WebLLMResearchProvider(FakeWeb(),lambda evidence,request:{'version':'1','evidence_urls':['https://evil.test/x']})
    assert p.research(EnvironmentResearchRequest('Node.js')).status=='NEEDS_RESEARCH'

def test_provider_rejects_command_like_llm_output():
    p=WebLLMResearchProvider(FakeWeb(),lambda evidence,request:{'version':'1','evidence_urls':['https://nodejs.org/'],'command':'sudo apt install node'})
    assert p.research(EnvironmentResearchRequest('Node.js')).status=='NEEDS_RESEARCH'

def test_provider_accepts_valid_artifact_only_from_official_host():
    p=WebLLMResearchProvider(FakeWeb(),lambda evidence,request:{
        'version':'22.1.0','evidence_urls':['https://nodejs.org/dist/index.json'],
        'artifact': {'platform':'linux','architecture':'x86_64','name':'node.tar.xz',
                     'download_url':'https://nodejs.org/dist/node.tar.xz'}})
    result=p.research(EnvironmentResearchRequest('Node.js'))
    assert result.status=='READY' and result.artifacts[0].architecture=='x86_64'
