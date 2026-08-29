from __future__ import annotations
from dataclasses import dataclass, field
import re
from .profiles import DEFAULT_PROFILES

@dataclass(frozen=True)
class EnvironmentPreparationIntent:
    environment: str
    profile: str
    requested_version: str|None = None
    constraints: dict = field(default_factory=dict)
    confirmation_mode: str = 'ask'

def detect_environment_intent(message: str) -> EnvironmentPreparationIntent|None:
    text=(message or '').lower().strip()
    for profile in DEFAULT_PROFILES.list():
        aliases=(profile.id,)+profile.aliases
        if any(re.search(r'(?<![\w])'+re.escape(alias.lower())+r'(?![\w])',text) for alias in aliases):
            version=(re.search(r'(?:version|v)\s*([0-9]+(?:\.[0-9]+)*)',text) or [None,None])[1]
            return EnvironmentPreparationIntent(profile.name,profile.id,version)
    return None
