"""Gap-driven resolution of typed environment artifacts."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ArtifactRequirement:
    component: str
    provider: str
    reason: str

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
        resolved=[]; missing=[]
        for req in self.requirements_for(gaps):
            result = self.jdk_provider.research() if req.component == "JDK" and self.jdk_provider else None
            if req.component != "JDK" and self.android_provider:
                result = self.android_provider.research(req.component)
            if result is None or (hasattr(result, "status") and result.status != "READY") or (hasattr(result, "trusted") and not result.trusted):
                missing.append(req)
            else: resolved.append(result)
        return tuple(resolved), tuple(missing)
