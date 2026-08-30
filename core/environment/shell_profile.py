from pathlib import Path
import os

class UserShellProfile:
    def __init__(self, shell=None, home=None):
        self.shell=(shell or os.environ.get('SHELL','')).rsplit('/',1)[-1].lower(); self.home=Path(home or Path.home())
    @property
    def path_file(self):
        return {'zsh':self.home/'.zshrc','fish':self.home/'.config/fish/config.fish'}.get(self.shell,self.home/'.profile')
