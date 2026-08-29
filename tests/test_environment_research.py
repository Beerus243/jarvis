from pathlib import Path
from core.environment.research import *
def test_research_uses_injected_metadata_only():
    researcher=EnvironmentResearcher(fetcher=lambda url:{'version':'fixture'})
    result=researcher.research(EnvironmentResearchRequest('Node.js'))
    assert result.status=='READY' and result.version=='fixture'
def test_unknown_or_unavailable_source_is_needs_research():
    assert EnvironmentResearcher().research(EnvironmentResearchRequest('unknown')).status=='NEEDS_RESEARCH'
def test_metadata_validation_rejects_wrong_host():
    source=DEFAULT_SOURCES.get('Node.js'); m=EnvironmentMetadata('1','stable','linux','x86_64','a','https://evil.test/a',None)
    assert validate_metadata(m,source)[0] is False
def test_checksum_and_cache(tmp_path):
    p=tmp_path/'x'; p.write_bytes(b'x'); import hashlib
    assert checksum_file(p,hashlib.sha256(b'x').hexdigest())
    cache=MetadataCache(tmp_path/'cache'); m=EnvironmentMetadata('1',None,'linux','x','a','https://nodejs.org/a',None); cache.save('x',m); assert cache.load('x')['version']=='1'
