from pathlib import Path
import os

class InstallationLock:
    def __init__(self, path=None): self.path=Path(path or Path.home()/'.cache/jarvis/flutter.install.lock')
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        try: self.fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        except FileExistsError: raise RuntimeError('Installation Flutter déjà en cours.')
        return self
    def __exit__(self,*args):
        os.close(self.fd); self.path.unlink(missing_ok=True)
