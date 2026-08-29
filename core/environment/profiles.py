from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class EnvironmentProfile:
    id: str
    name: str
    aliases: tuple[str, ...] = ()
    description: str = ''
    requirements: tuple[str, ...] = ()
    dependencies: dict[str, tuple[str, ...]] = field(default_factory=dict)

class EnvironmentProfileRegistry:
    def __init__(self, profiles=()):
        self._profiles={}
        for profile in profiles: self.register(profile)
    def register(self, profile):
        if not profile.id or not profile.name or profile.id in self._profiles: raise ValueError('Profil invalide ou déjà enregistré.')
        self._profiles[profile.id]=profile
    def get(self, profile_id): return self._profiles.get(profile_id)
    def resolve(self, value):
        key=str(value).lower().strip()
        return next((p for p in self._profiles.values() if key == p.id.lower() or key in {a.lower() for a in p.aliases}), None)
    def list(self): return tuple(self._profiles.values())

DEFAULT_PROFILES=EnvironmentProfileRegistry([
    EnvironmentProfile('flutter_development','Flutter Development',('flutter','flutter development'),requirements=('flutter','dart','java','javac','android_sdk','adb','android_studio','git')),
    EnvironmentProfile('node','Node.js',('node','nodejs'),requirements=('node','npm','git')),
    EnvironmentProfile('nextjs','Next.js',('next','next.js'),requirements=('node','npm','git'),dependencies={'node':('npm',)}),
    EnvironmentProfile('java','Java Development',('java','jdk'),requirements=('java','javac')),
])
