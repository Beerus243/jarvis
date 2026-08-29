from __future__ import annotations
from pathlib import Path
import tarfile, zipfile

class SecureArchiveExtractor:
    def _target(self,destination,name):
        root=Path(destination).expanduser().resolve(); member=Path(name)
        if member.is_absolute(): raise ValueError('Chemin absolu interdit.')
        target=(root/member).resolve()
        if target != root and root not in target.parents: raise ValueError('Archive path traversal rejected')
        return root,target
    def extract(self,archive,destination,archive_type=None):
        archive=Path(archive); destination=Path(destination).expanduser().resolve(); destination.mkdir(parents=True,exist_ok=True); kind=(archive_type or '').lower() or ('zip' if zipfile.is_zipfile(archive) else 'tar')
        try:
            if kind.startswith('zip'):
                with zipfile.ZipFile(archive) as z:
                    for info in z.infolist():
                        _,target=self._target(destination,info.filename)
                        if info.is_dir(): target.mkdir(parents=True,exist_ok=True); continue
                        target.parent.mkdir(parents=True,exist_ok=True)
                        with z.open(info) as src,target.open('wb') as dst: dst.write(src.read())
            else:
                with tarfile.open(archive,'r:*') as tar:
                    for info in tar.getmembers():
                        root,target=self._target(destination,info.name)
                        if info.issym() or info.islnk():
                            link=(target.parent/info.linkname).resolve()
                            if link != root and root not in link.parents: raise ValueError('Symlink escape rejected')
                        tar.extract(info,destination)
            return True
        except Exception: return False
