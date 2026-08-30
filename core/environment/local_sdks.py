from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os, re, platform

@dataclass(frozen=True)
class LocalSDKCandidate:
    name: str; root: Path; version: str|None; architecture: str|None
    flutter: bool; dart: bool; path_configured: bool; state: str; trust: str='LOCAL_UNVERIFIED'

class LocalSDKDiscovery:
    def __init__(self, roots=None, max_depth=3):
        home=Path.home(); self.roots=[Path(p).expanduser() for p in (roots or [home/'development/flutter',home/'development',home/'dev/flutter',home/'projects/flutter',home/'workspace/flutter',home/'.local/share/jarvis/environments/flutter',home/'flutter'])]; self.max_depth=max_depth
    def _roots(self):
        seen=set()
        for root in self.roots:
            if not root.exists(): continue
            candidates=[root]
            if root.is_dir(): candidates += [p for p in root.iterdir() if p.is_dir()]
            for candidate in candidates:
                resolved=candidate.resolve()
                if resolved not in seen and len(resolved.parts)-len(root.resolve().parts)<=self.max_depth: seen.add(resolved); yield resolved
    def inspect(self, root):
        root=Path(root).expanduser().resolve(); flutter=root/'bin/flutter'; dart=root/'bin/dart'
        has_flutter=flutter.is_file(); has_dart=dart.is_file()
        version=None
        for f in (root/'version',root/'VERSION'):
            if f.is_file():
                match=re.search(r'\d+\.\d+(?:\.\d+)?',f.read_text(errors='ignore')); version=match.group(0) if match else None; break
        if version is None:
            match=re.search(r'\d+\.\d+(?:\.\d+)?',root.name); version=match.group(0) if match else None
        configured=str((root/'bin').resolve()) in os.environ.get('PATH','').split(os.pathsep)
        state='READY' if has_flutter and has_dart and configured else 'EXTRACTED_NOT_CONFIGURED' if has_flutter and has_dart else 'PARTIAL' if has_flutter or has_dart else 'BROKEN'
        arch='x86_64' if platform.machine().lower() in {'x86_64','amd64'} else platform.machine() or None
        return LocalSDKCandidate('Flutter',root,version,arch,has_flutter,has_dart,configured,state)
    def discover(self, architecture=None):
        items=[self.inspect(root) for root in self._roots()]
        items=[i for i in items if i.flutter or i.dart]
        if architecture: items=[i for i in items if i.architecture==architecture]
        return sorted(items,key=lambda i:(i.state=='READY',i.version or '',str(i.root)),reverse=True)
