from pathlib import Path
import os

class ConfigureUserPath:
    def __init__(self, path_file=None, allowed_root=None):
        self.path_file=Path(path_file or Path.home()/'.profile').expanduser(); self.allowed_root=Path(allowed_root or Path.home()).expanduser().resolve()
    def apply(self, bin_path):
        bin_path=str(Path(bin_path).expanduser().resolve())
        if not Path(bin_path).is_relative_to(self.allowed_root): return False
        old=self.path_file.read_text(encoding='utf-8') if self.path_file.exists() else ''
        marker=f'export PATH="{bin_path}:$PATH"'
        if bin_path in old: return True
        if self.path_file.exists(): self.path_file.with_suffix(self.path_file.suffix+'.bak').write_text(old,encoding='utf-8')
        self.path_file.parent.mkdir(parents=True,exist_ok=True); self.path_file.write_text(old + ('\n' if old and not old.endswith('\n') else '') + marker + '\n',encoding='utf-8')
        return True
