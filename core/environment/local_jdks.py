from dataclasses import dataclass
from pathlib import Path
import os, re
@dataclass(frozen=True)
class LocalJDKCandidate:
    root: Path; version: str|None; java: bool; javac: bool; java_home: bool; path_configured: bool; state: str='UNKNOWN'
class LocalJDKDiscovery:
    def __init__(self, roots=None):
        home=Path.home(); self.roots=[Path(p).expanduser() for p in (roots or [os.getenv('JAVA_HOME',''),home/'.local/share/jarvis/environments/jdk',home/'development/jdk']) if p]
    def discover(self):
        out=[]
        for base in self.roots:
            candidates=[base]+([p for p in base.iterdir() if p.is_dir()] if base.is_dir() else [])
            for root in candidates:
                java=(root/'bin/java').is_file(); javac=(root/'bin/javac').is_file()
                if not (java or javac): continue
                m=re.search(r'\d+(?:\.\d+)+',root.name); version=m.group(0) if m else None
                configured=os.getenv('JAVA_HOME')==str(root); path=str((root/'bin').resolve()) in os.getenv('PATH','').split(os.pathsep)
                out.append(LocalJDKCandidate(root,version,java,javac,configured,path,'READY' if java and javac else 'PARTIAL'))
        return out
