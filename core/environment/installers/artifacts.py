from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .contracts import TrustedSource
@dataclass(frozen=True)
class InstallationArtifact:
    name:str; version:str; platform:str; architecture:str; source:TrustedSource; archive_type:str; destination:Path; checksum:str|None=None; evidence:tuple[str,...]=()
    def validate(self):
        if self.platform not in {'linux'} or self.architecture not in {'x86_64','aarch64'}: return False
        home=Path.home().resolve(); dest=self.destination.expanduser().resolve()
        return (dest==home or home in dest.parents) and self.source.approved()

@dataclass
class InstallationStep:
    id:str; requirement:str; action_type:str; order:int; dependencies:list[str]; risk_level:str='MEDIUM'; requires_confirmation:bool=True; rollback_supported:bool=False
@dataclass
class InstallationPlan:
    requirement:str; steps:list[InstallationStep]; blocked:bool=False; reason:str|None=None
