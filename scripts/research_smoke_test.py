#!/usr/bin/env python3
"""Read-only smoke test for the Web + Groq research boundary.

The script never downloads an artifact or executes a command.  A JSON search
endpoint can be supplied with JARVIS_SEARCH_ENDPOINT; otherwise the official
metadata URL is used and a provider-specific JSON endpoint is required.
"""
import os
import sys

from openai import OpenAI

from config.settings import MODEL
from core.environment import (DEFAULT_SOURCES, EnvironmentResearchRequest,
                              GroqResearchInterpreter, WebLLMResearchProvider,
                              WebSearchClient)


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: research_smoke_test.py flutter|node|java')
    name = sys.argv[1].lower()
    source = next((item for item in DEFAULT_SOURCES.list() if name in item.name.lower()), None)
    if source is None:
        raise SystemExit(f'environnement inconnu: {name}')
    key = os.getenv('GROQ_API_KEY')
    if not key:
        raise SystemExit('GROQ_API_KEY introuvable (aucune requête effectuée).')
    endpoint = os.getenv('JARVIS_SEARCH_ENDPOINT', source.metadata_url)
    client = OpenAI(api_key=key, base_url='https://api.groq.com/openai/v1')
    provider = WebLLMResearchProvider(
        WebSearchClient(timeout=10), GroqResearchInterpreter(client, os.getenv('MODEL', MODEL))
    )
    result = provider.research(EnvironmentResearchRequest(source.name))
    print({'environment': source.name, 'status': result.status, 'version': result.version,
           'confidence': result.confidence, 'artifacts': [item.__dict__ for item in result.artifacts],
           'evidence': result.verification, 'warnings': result.warnings, 'endpoint': endpoint})


if __name__ == '__main__':
    main()
