from .contracts import EnvironmentInstaller
class InstallerRegistry:
    def __init__(self): self._items={}
    def register(self, installer):
        if not isinstance(installer, EnvironmentInstaller) or installer.requirement in self._items: raise ValueError('Installer invalide ou déjà enregistré.')
        self._items[installer.requirement]=installer
    def get(self, requirement): return self._items.get(requirement)
    def list(self): return tuple(self._items.values())
