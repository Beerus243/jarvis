from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from urllib.parse import urlparse
import hashlib, json, time

@dataclass(frozen=True)
class OfficialSource:
    name:str; domain:str; base_url:str; metadata_url:str; artifact_domains:tuple[str,...]=(); documentation_url:str|None=None
    def accepts(self,url):
        p=urlparse(url); return p.scheme=='https' and p.hostname in ((self.domain,)+self.artifact_domains)
    def accepts_documentation(self, url):
        """Return whether *url* is an HTTPS page belonging to this source."""
        p = urlparse(url)
        hosts = (self.domain,) + self.artifact_domains
        if self.documentation_url:
            doc_host = urlparse(self.documentation_url).hostname
            hosts += (doc_host,) if doc_host else ()
        return p.scheme == 'https' and p.hostname in hosts

@dataclass
class EnvironmentMetadata:
    version:str; channel:str|None; platform:str; architecture:str; artifact:str; download_url:str; checksum:str|None; checksum_algorithm:str='sha256'; source:str=''; release_date:str|None=None; verification_method:str|None=None

@dataclass(frozen=True)
class EnvironmentResearchRequest:
    environment:str; requirements:tuple[str,...]=(); platform:str='linux'; architecture:str='x86_64'; preferred_channel:str='stable'

@dataclass
class EnvironmentResearchResult:
    official_sources:list[OfficialSource]=field(default_factory=list); version:str|None=None; artifacts:list[EnvironmentMetadata]=field(default_factory=list); dependencies:list[str]=field(default_factory=list); verification:dict=field(default_factory=dict); confidence:float=0.0; warnings:list[str]=field(default_factory=list); status:str='NEEDS_RESEARCH'; provider_state:str='NEEDS_RESEARCH'

@dataclass(frozen=True)
class ResearchCandidate:
    source: str; claim: str; value: str; evidence: str; confidence: float=0.0

class ResearchProvider:
    def research(self, query: str): raise NotImplementedError

class OfficialSourceRegistry:
    def __init__(self): self._sources={}
    def register(self,source):
        if source.name in self._sources: raise ValueError('Source déjà enregistrée.')
        self._sources[source.name]=source
    def get(self,name): return self._sources.get(name)
    def list(self): return tuple(self._sources.values())

DEFAULT_SOURCES=OfficialSourceRegistry()
for _source in (OfficialSource('Flutter','storage.googleapis.com','https://storage.googleapis.com/flutter_infra_release/releases/','https://docs.flutter.dev/install/archive',('storage.googleapis.com',),'https://docs.flutter.dev/'), OfficialSource('Node.js','nodejs.org','https://nodejs.org/dist/','https://nodejs.org/dist/index.json',('nodejs.org',),'https://nodejs.org/'), OfficialSource('Eclipse Adoptium','adoptium.net','https://api.adoptium.net/','https://api.adoptium.net/v3/info/available_releases',('api.adoptium.net',),'https://adoptium.net/')):
    DEFAULT_SOURCES.register(_source)

def validate_metadata(metadata:EnvironmentMetadata, source:OfficialSource, *, expected_architecture=None):
    if not source.accepts(metadata.download_url): return False,'SOURCE_REJECTED'
    if expected_architecture and metadata.architecture != expected_architecture: return False,'ARCHITECTURE_MISMATCH'
    if not metadata.version or not metadata.artifact: return False,'METADATA_INCOMPLETE'
    return True,None

class EnvironmentResearcher:
    def __init__(self, registry=DEFAULT_SOURCES, fetcher=None): self.registry=registry; self.fetcher=fetcher
    def research(self, request:EnvironmentResearchRequest):
        source=next((s for s in self.registry.list() if s.name.lower().startswith(request.environment.lower()) or request.environment.lower() in s.name.lower()),None)
        if not source or not self.fetcher: return EnvironmentResearchResult(warnings=['Source officielle ou mécanisme de recherche indisponible.'])
        try: payload=self.fetcher(source.metadata_url)
        except Exception as exc: return EnvironmentResearchResult(official_sources=[source],warnings=[str(exc)])
        if not isinstance(payload,dict) or not payload.get('version'): return EnvironmentResearchResult(official_sources=[source],warnings=['Métadonnées incomplètes.'])
        return EnvironmentResearchResult(official_sources=[source],version=str(payload['version']),confidence=1.0,status='READY',warnings=[])

def checksum_file(path, expected, algorithm='sha256'):
    if not expected: return False
    h=hashlib.new(algorithm)
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest().lower()==expected.lower()

class MetadataCache:
    def __init__(self,directory=None,ttl=3600): self.directory=Path(directory or Path.home()/'.cache/jarvis/environment'); self.ttl=ttl
    def save(self,key,metadata): self.directory.mkdir(parents=True,exist_ok=True); (self.directory/f'{key}.json').write_text(json.dumps({'timestamp':time.time(),'metadata':asdict(metadata)}),encoding='utf-8')
    def load(self,key):
        path=self.directory/f'{key}.json'
        if not path.exists() or time.time()-path.stat().st_mtime>self.ttl: return None
        return json.loads(path.read_text(encoding='utf-8')).get('metadata')

    def save_official(self, key, metadata, *, source, evidence=()):
        """Persist metadata tagged as cached official evidence."""
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = {'state': 'CACHED_OFFICIAL_METADATA', 'timestamp': time.time(),
                   'source': source, 'evidence': list(evidence), 'metadata': metadata}
        (self.directory / f'{key}.json').write_text(json.dumps(payload), encoding='utf-8')

    def load_official(self, key):
        path = self.directory / f'{key}.json'
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
            if payload.get('state') != 'CACHED_OFFICIAL_METADATA': return None
            if time.time() - float(payload.get('timestamp', 0)) > self.ttl: return None
            if not payload.get('metadata') or not payload.get('source'): return None
            return payload
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return None
