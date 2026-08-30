from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os, shutil

@dataclass(frozen=True)
class AndroidSDKStatus:
    root: Path|None; sdk: str; platform_tools: str; adb: str; build_tools: str
    platforms: str; cmdline_tools: str; licenses: str; adb_in_path: bool
    def to_dict(self): return self.__dict__.copy()

class AndroidSDKDiscovery:
    def __init__(self, roots=None):
        home=Path.home(); self.roots=[Path(p).expanduser() for p in (roots or [os.getenv('ANDROID_SDK_ROOT',''),os.getenv('ANDROID_HOME',''),home/'Android/Sdk',home/'Android/sdk']) if p]
    def discover(self):
        root=next((p.resolve() for p in self.roots if p.is_dir()),None)
        if root is None: return AndroidSDKStatus(None,'SDK_MISSING','MISSING','MISSING','MISSING','MISSING','MISSING','UNKNOWN',False)
        platform_tools=(root/'platform-tools').is_dir(); adb_file=root/'platform-tools/adb'; adb_path=shutil.which('adb'); adb=adb_path or (str(adb_file) if adb_file.is_file() and os.access(adb_file,os.X_OK) else 'MISSING')
        build=any(p.is_dir() for p in (root/'build-tools').glob('*')) if (root/'build-tools').is_dir() else False
        platforms=any(p.is_dir() for p in (root/'platforms').glob('*')) if (root/'platforms').is_dir() else False
        cmd_root = root / 'cmdline-tools'
        cmd=any((p/'bin/sdkmanager').is_file() and os.access(p/'bin/sdkmanager', os.X_OK)
                for p in cmd_root.glob('*') if p.is_dir()) if cmd_root.is_dir() else False
        licenses=(root/'licenses').is_dir() and any((root/'licenses').iterdir())
        return AndroidSDKStatus(root,'PRESENT' if platform_tools else 'SDK_PARTIAL','PRESENT' if platform_tools else 'MISSING','PRESENT' if adb!='MISSING' else 'MISSING','PRESENT' if build else 'MISSING','PRESENT' if platforms else 'MISSING','PRESENT' if cmd else 'MISSING','ACCEPTED' if licenses else 'UNKNOWN',bool(adb_path))
