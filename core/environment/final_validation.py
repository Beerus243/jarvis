"""Structured final Flutter/Android toolchain validation."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class FinalToolchainReport:
    components: dict
    state: str
    gaps: tuple[str, ...]
    def to_dict(self): return {"components": dict(self.components), "state": self.state, "gaps": list(self.gaps)}

def validate_final_toolchain(*, flutter=False, dart=False, java=False, javac=False,
                             java_home=False, android_sdk=False, adb=False,
                             build_tools=False, platforms=False, cmdline_tools=False,
                             licenses=False, path=False, flutter_doctor=False):
    values = locals().copy()
    gaps = tuple(name.upper() for name, value in values.items() if not value)
    return FinalToolchainReport(values, "ENVIRONMENT_READY" if not gaps else "PARTIAL", gaps)
