from __future__ import annotations
from dataclasses import dataclass
import requests
from .research import (EnvironmentResearchRequest, EnvironmentResearchResult,
                       EnvironmentMetadata, ResearchCandidate, DEFAULT_SOURCES,
                       validate_metadata)
import json

@dataclass(frozen=True)
class WebSearchResult:
    title: str; url: str; snippet: str=''; source: str=''

class WebSearchClient:
    def __init__(self, session=None, timeout=5): self.session=session or requests; self.timeout=timeout
    def search(self, query: str, endpoint: str, *, source=None):
        # Never allow an arbitrary URL supplied by an LLM/user to become a
        # network target.  The endpoint must be an HTTPS official source.
        if source is not None and not source.accepts_documentation(endpoint):
            raise ValueError('Endpoint de recherche non officiel.')
        if source is None or not endpoint.startswith('https://'):
            raise ValueError('Endpoint HTTPS requis.')
        response=self.session.get(endpoint, params={'q':query}, timeout=self.timeout)
        response.raise_for_status(); data=response.json()
        if not isinstance(data, dict):
            return []
        results = data.get('results', [])
        if not isinstance(results, list):
            return []
        return [WebSearchResult(str(x.get('title','')), str(x.get('url','')), str(x.get('snippet','')),
                                str(x.get('source',''))) for x in results if isinstance(x, dict)]


class GroqResearchInterpreter:
    """Small adapter around the existing OpenAI-compatible Groq client.

    It only requests JSON metadata; it never exposes a command-execution tool.
    The client is injected so tests remain entirely offline.
    """
    def __init__(self, client, model):
        self.client, self.model = client, model

    def __call__(self, evidence, request):
        prompt = {
            'environment': request.environment,
            'platform': request.platform,
            'architecture': request.architecture,
            'evidence': [getattr(item, '__dict__', item) for item in evidence],
        }
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={'type': 'json_object'},
            messages=[
                {'role': 'system', 'content': 'Return JSON metadata only. Never return shell commands.'},
                {'role': 'user', 'content': json.dumps(prompt, ensure_ascii=False)},
            ],
        )
        content = response.choices[0].message.content
        return json.loads(content)

class WebLLMResearchProvider:
    _DANGEROUS = ('sudo','apt','dnf','pacman','curl','wget','bash','sh','chmod','rm','mv','cp','tar')
    def __init__(self, web_client, interpreter, registry=DEFAULT_SOURCES):
        self.web=web_client; self.interpreter=interpreter; self.registry=registry

    @classmethod
    def _contains_dangerous_instruction(cls, value):
        if isinstance(value, dict):
            return any(cls._contains_dangerous_instruction(v) for v in value.values())
        if isinstance(value, (list, tuple)):
            return any(cls._contains_dangerous_instruction(v) for v in value)
        if isinstance(value, str):
            import re
            # Match shell-like words, not harmless substrings in filenames
            # (for example ``node.tar.xz``).
            return any(re.search(r'(?:^|[\s;|&])'+re.escape(token)+r'(?:\s|$|[;|&])', value.lower()) for token in cls._DANGEROUS)
        return False
    def research(self, request: EnvironmentResearchRequest):
        source=next((s for s in self.registry.list() if request.environment.lower() in s.name.lower()),None)
        if not source: return EnvironmentResearchResult(warnings=['Source officielle inconnue.'])
        try:
            query = f'current official stable {request.environment} {request.platform} {request.architecture}'
            try:
                evidence=self.web.search(query, source.metadata_url, source=source)
            except TypeError:
                # Keep compatibility with the minimal ``search(query, url)``
                # interface used by existing clients.
                evidence=self.web.search(query, source.metadata_url)
            payload=self.interpreter(evidence,request)
        except Exception as exc:
            return EnvironmentResearchResult(official_sources=[source],warnings=[f'Recherche indisponible: {exc}'])
        if not isinstance(payload,dict) or self._contains_dangerous_instruction(payload):
            return EnvironmentResearchResult(official_sources=[source],warnings=['Réponse de recherche rejetée.'])
        version = payload.get('version')
        evidence_urls = payload.get('evidence_urls', [])
        if not version or not isinstance(evidence_urls, list) or not evidence_urls:
            return EnvironmentResearchResult(official_sources=[source],warnings=['Preuves officielles incomplètes.'])
        if not all(isinstance(url, str) and source.accepts_documentation(url) for url in evidence_urls):
            return EnvironmentResearchResult(official_sources=[source],warnings=['Preuve non officielle rejetée.'])
        artifacts=[]
        artifact_data=payload.get('artifact')
        if isinstance(artifact_data, dict):
            required=('platform','architecture','name','download_url')
            if not all(artifact_data.get(k) for k in required):
                return EnvironmentResearchResult(official_sources=[source],warnings=['Artifact incomplet.'])
            metadata=EnvironmentMetadata(str(version), payload.get('channel'), str(artifact_data['platform']),
                                         str(artifact_data['architecture']), str(artifact_data['name']),
                                         str(artifact_data['download_url']), artifact_data.get('checksum'),
                                         str(artifact_data.get('checksum_algorithm','sha256')), source.name,
                                         payload.get('release_date'), 'official-evidence')
            valid, reason=validate_metadata(metadata, source, expected_architecture=request.architecture)
            if not valid:
                return EnvironmentResearchResult(official_sources=[source],warnings=[reason])
            artifacts.append(metadata)
        try: confidence=float(payload.get('confidence',0.0))
        except (TypeError, ValueError): confidence=0.0
        confidence=max(0.0,min(1.0,confidence))
        verification={'evidence': [ResearchCandidate(source.name, 'version', str(version), url, confidence) for url in evidence_urls]}
        return EnvironmentResearchResult(official_sources=[source],version=str(version),artifacts=artifacts,
                                         verification=verification,confidence=confidence,status='READY')

class FlutterResearchProvider(WebLLMResearchProvider):
    """Strict Flutter adapter: no artifact means no installable result."""
    def research(self, request):
        result = super().research(request)
        if result.status != 'READY' or not result.artifacts:
            result.status = 'NEEDS_RESEARCH'
            result.warnings.append('Artefact Flutter ou checksum officiel manquant.')
            return result
        artifact = result.artifacts[0]
        if not artifact.checksum or len(artifact.checksum) != 64:
            result.status = 'NEEDS_RESEARCH'; result.warnings.append('SHA-256 Flutter absent ou invalide.')
        if artifact.platform != 'linux' or artifact.architecture != request.architecture:
            result.status = 'NEEDS_RESEARCH'; result.warnings.append('Plateforme/architecture Flutter incohérente.')
        return result
