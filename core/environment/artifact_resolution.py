"""Gap-driven resolution of typed environment artifacts."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class ResolutionState(str, Enum):
    AVAILABLE='AVAILABLE'; NOT_AVAILABLE='NOT_AVAILABLE'; NETWORK_UNAVAILABLE='NETWORK_UNAVAILABLE'; INVALID_ARTIFACT='INVALID_ARTIFACT'; NEEDS_RESEARCH='NEEDS_RESEARCH'

@dataclass(frozen=True)
class ArtifactRequirement:
    component: str
    provider: str
    reason: str

@dataclass(frozen=True)
class ArtifactResolutionResult:
    artifacts: tuple = ()
    missing: tuple = ()
    state: ResolutionState = ResolutionState.NEEDS_RESEARCH

class ArtifactResolutionEngine:
    def __init__(self, jdk_provider=None, android_provider=None):
        self.jdk_provider, self.android_provider = jdk_provider, android_provider

    def requirements_for(self, gaps):
        out=[]
        if any(g in gaps for g in ("MISSING_JAVAC", "MISSING_JDK")):
            out.append(ArtifactRequirement("JDK", "Eclipse Adoptium", "javac/JDK manquant"))
        for gap, component in (("MISSING_ANDROID_PLATFORM_TOOLS", "platform-tools"),
                               ("MISSING_ADB", "platform-tools"),
                               ("MISSING_ANDROID_BUILD_TOOLS", "build-tools"),
                               ("MISSING_ANDROID_PLATFORM", "platforms"),
                               ("MISSING_ANDROID_CMDLINE_TOOLS", "cmdline-tools")):
            if gap in gaps and not any(r.component == component for r in out):
                out.append(ArtifactRequirement(component, "Android Developers", gap))
        return tuple(out)

    def resolve(self, gaps):
        result = self.resolve_detailed(gaps)
        return result.artifacts, result.missing

    def resolve_detailed(self, gaps):
        resolved=[]; missing=[]; provider_states=[]
        for req in self.requirements_for(gaps):
            result = self.jdk_provider.research() if req.component == "JDK" and self.jdk_provider else None
            if req.component != "JDK" and self.android_provider:
                result = self.android_provider.research(req.component)
            if result is None or (hasattr(result, "status") and result.status != "READY") or (hasattr(result, "trusted") and not result.trusted):
                missing.append(req)
                provider_states.append(getattr(result, 'provider_state', None))
            else: resolved.append(result)
        states = [getattr(item, 'provider_state', None) for item in resolved] + provider_states
        state = ResolutionState.AVAILABLE if resolved and not missing else ResolutionState.NETWORK_UNAVAILABLE if 'NETWORK_UNAVAILABLE' in states else ResolutionState.NOT_AVAILABLE if missing else ResolutionState.AVAILABLE
        return ArtifactResolutionResult(tuple(resolved), tuple(missing), state)
