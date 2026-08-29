from core.environment import FlutterResearchProvider, EnvironmentResearchRequest
from core.environment.installers.flutter_installer import FlutterInstaller

class Web:
    def search(self,*args,**kwargs): return []

def payload(**overrides):
    data={'version':'3.24.0','evidence_urls':['https://docs.flutter.dev/install/archive'],
          'artifact':{'platform':'linux','architecture':'x86_64','name':'flutter_linux.tar.xz','download_url':'https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.24.0-stable.tar.xz','checksum':'a'*64}}
    data.update(overrides); return data
def provider(p): return FlutterResearchProvider(Web(),lambda e,r:p)
def test_valid_official_flutter_result():
    result=provider(payload()).research(EnvironmentResearchRequest('Flutter'))
    assert result.status=='READY' and result.artifacts[0].checksum=='a'*64
def test_missing_checksum_is_needs_research():
    p=payload(); p['artifact'].pop('checksum'); assert provider(p).research(EnvironmentResearchRequest('Flutter')).status=='NEEDS_RESEARCH'
def test_invalid_architecture_is_rejected():
    p=payload(); p['artifact']['architecture']='aarch64'; assert provider(p).research(EnvironmentResearchRequest('Flutter')).status=='NEEDS_RESEARCH'
def test_invalid_domain_is_rejected():
    p=payload(); p['artifact']['download_url']='https://evil.example/flutter.tar.xz'; assert provider(p).research(EnvironmentResearchRequest('Flutter')).status=='NEEDS_RESEARCH'
def test_http_evidence_is_rejected():
    p=payload(evidence_urls=['http://docs.flutter.dev/install/archive']); assert provider(p).research(EnvironmentResearchRequest('Flutter')).status=='NEEDS_RESEARCH'
def test_missing_evidence_is_rejected():
    p=payload(evidence_urls=[]); assert provider(p).research(EnvironmentResearchRequest('Flutter')).status=='NEEDS_RESEARCH'
def test_hallucinated_command_is_rejected():
    p=payload(command='sudo apt install flutter'); assert provider(p).research(EnvironmentResearchRequest('Flutter')).status=='NEEDS_RESEARCH'
def test_dynamic_version_is_preserved():
    result=provider(payload(version='3.30.1')).research(EnvironmentResearchRequest('Flutter')); assert result.version=='3.30.1'
def test_validated_research_becomes_artifact_with_evidence():
    result=provider(payload()).research(EnvironmentResearchRequest('Flutter'))
    artifact=FlutterInstaller().artifact_from_research(result)
    assert artifact and artifact.version=='3.24.0' and artifact.evidence
