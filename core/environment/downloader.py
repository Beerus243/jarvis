from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib, tempfile
from urllib.parse import urlparse
import requests
from .installers.artifacts import InstallationArtifact
from .installers.security import validate_source

@dataclass(frozen=True)
class DownloadResult:
    success: bool; path: Path|None = None; error: str|None = None; bytes_written: int = 0

class ArtifactDownloader:
    def __init__(self, cache_dir=None, max_size=2*1024*1024*1024, session=None, timeout=30):
        self.cache_dir=Path(cache_dir or Path.home()/'.cache/jarvis/environment').expanduser(); self.max_size=max_size; self.session=session or requests; self.timeout=timeout
    def download(self, artifact: InstallationArtifact):
        url=artifact.source.url or ''
        if not validate_source(artifact.source) or urlparse(url).scheme != 'https': return DownloadResult(False,error='Source de téléchargement non autorisée.')
        self.cache_dir.mkdir(parents=True,exist_ok=True); current=url
        try:
            for _ in range(4):
                response=self.session.get(current,stream=True,allow_redirects=False,timeout=self.timeout)
                if getattr(response,'is_redirect',False) or getattr(response,'is_permanent_redirect',False) or response.status_code in (301,302,303,307,308):
                    location=response.headers.get('Location')
                    if not location or urlparse(location).scheme != 'https' or urlparse(location).hostname not in ('storage.googleapis.com','nodejs.org','adoptium.net','api.adoptium.net'): return DownloadResult(False,error='Redirection vers une source non autorisée.')
                    current=location; continue
                if response.status_code >= 400: return DownloadResult(False,error=f'HTTP {response.status_code}.')
                length=response.headers.get('Content-Length')
                if length and int(length)>self.max_size: return DownloadResult(False,error='Artefact trop volumineux.')
                fd,tmp=tempfile.mkstemp(prefix='.jarvis-',dir=self.cache_dir); import os; os.close(fd); total=0; digest=hashlib.sha256()
                with open(tmp,'wb') as stream:
                    for chunk in response.iter_content(1024*1024):
                        if not chunk: continue
                        total += len(chunk)
                        if total > self.max_size: Path(tmp).unlink(missing_ok=True); return DownloadResult(False,error='Limite de taille dépassée.')
                        stream.write(chunk); digest.update(chunk)
                if artifact.source.checksum and digest.hexdigest().lower()!=artifact.source.checksum.lower(): Path(tmp).unlink(missing_ok=True); return DownloadResult(False,error='Checksum SHA-256 invalide.')
                final=self.cache_dir / artifact.name; Path(tmp).replace(final); return DownloadResult(True,final,None,total)
            return DownloadResult(False,error='Trop de redirections.')
        except Exception as exc: return DownloadResult(False,error=str(exc))
