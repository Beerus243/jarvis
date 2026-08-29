from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib, re, tarfile, zipfile
from .installers.artifacts import InstallationArtifact
from .installers.contracts import TrustedSource

@dataclass(frozen=True)
class LocalArtifactCandidate:
    path: Path; filename: str; format: str; product: str = 'flutter'; version: str|None = None
    architecture: str|None = None; size: int = 0; validation_status: str = 'UNKNOWN'
    reason: str|None = None; checksum: str|None = None; checksum_status: str = 'LOCAL_UNVERIFIED'

class LocalArtifactDiscovery:
    EXTENSIONS={'.tar.xz':'tar.xz','.tar.gz':'tar.gz','.zip':'zip'}
    def __init__(self, search_paths=None, max_depth=3):
        home=Path.home(); self.search_paths=[Path(p).expanduser() for p in (search_paths or [home/'Downloads',home/'Téléchargements',home/'.cache',home/'.local/share/jarvis'])]; self.max_depth=max_depth
    def _files(self, root):
        if not root.is_dir(): return []
        base_parts=len(root.resolve().parts); found=[]
        for path in root.rglob('*'):
            try: depth=len(path.resolve().parts)-base_parts
            except OSError: continue
            if depth<=self.max_depth and path.is_file() and self._format(path): found.append(path)
        return found
    @classmethod
    def _format(cls,path):
        name=path.name.lower()
        for ext,kind in cls.EXTENSIONS.items():
            if name.endswith(ext): return kind
        return None
    @staticmethod
    def _metadata(path,kind):
        names=[]; unsafe=None
        try:
            if kind=='zip':
                with zipfile.ZipFile(path) as archive:
                    for info in archive.infolist(): names.append(info.filename)
            else:
                with tarfile.open(path,'r:*') as archive:
                    for info in archive.getmembers():
                        names.append(info.name)
                        if info.issym() or info.islnk():
                            target=(Path(info.name).parent/ info.linkname).resolve()
                            if str(target).startswith('/'): unsafe='symlink escape'
        except Exception as exc: return [],str(exc)
        for name in names:
            p=Path(name)
            if p.is_absolute() or '..' in p.parts: unsafe='archive path traversal'
        return names,unsafe
    def inspect(self,path):
        path=Path(path).expanduser(); kind=self._format(path)
        if not kind: return LocalArtifactCandidate(path,path.name,'unknown',validation_status='INVALID',reason='Format non supporté.')
        names,unsafe=self._metadata(path,kind)
        if unsafe: return LocalArtifactCandidate(path,path.name,kind,validation_status='INVALID',reason=unsafe,size=path.stat().st_size if path.exists() else 0)
        has_flutter=any(name.rstrip('/').endswith('flutter/bin/flutter') for name in names)
        has_dart=any(name.rstrip('/').endswith('flutter/bin/dart') for name in names)
        if not has_flutter or not has_dart:
            return LocalArtifactCandidate(path,path.name,kind,validation_status='INVALID',reason='Entrées Flutter/Dart absentes',size=path.stat().st_size)
        version_match=re.search(r'(?:flutter[_-])?(\d+\.\d+(?:\.\d+)?)',path.name.lower())
        arch='x86_64' if re.search(r'(linux[_-]?x64|x86_64|amd64)',path.name.lower()) else None
        return LocalArtifactCandidate(path,path.name,kind,version=version_match.group(1) if version_match else None,architecture=arch,size=path.stat().st_size,validation_status='VALID',checksum_status='LOCAL_UNVERIFIED')
    def discover(self, *, requested_version=None, architecture=None):
        candidates=[self.inspect(path) for root in self.search_paths for path in self._files(root)]
        candidates=[c for c in candidates if c.validation_status=='VALID']
        if requested_version: candidates=[c for c in candidates if c.version==requested_version]
        if architecture: candidates=[c for c in candidates if c.architecture in (architecture,None)]
        return sorted(candidates,key=lambda c:(c.architecture is not None,c.version or '',str(c.path)),reverse=True)
    @staticmethod
    def checksum(path):
        digest=hashlib.sha256();
        with Path(path).open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''): digest.update(chunk)
        return digest.hexdigest()
    def to_installation_artifact(self,candidate,destination):
        if candidate.validation_status!='VALID': return None
        checksum=self.checksum(candidate.path)
        source=TrustedSource('local',candidate.version or 'unknown',candidate.format,None,checksum,candidate.architecture, str(candidate.path))
        return InstallationArtifact(candidate.filename,candidate.version or 'unknown','linux',candidate.architecture or 'unknown',source,candidate.format,Path(destination),checksum)
