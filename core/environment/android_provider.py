"""Official Android component metadata provider (no shell commands)."""
from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass(frozen=True)
class AndroidArtifact:
    component: str
    version: str | None
    platform: str
    architecture: str | None
    download_url: str | None
    checksum: str | None
    source_url: str
    evidence_urls: tuple[str, ...] = ()
    checksum_algorithm: str = "sha256"

    @property
    def trusted(self):
        parsed = urlparse(self.download_url or "")
        return (parsed.scheme == "https" and parsed.hostname in {"dl.google.com", "developer.android.com"}
                and bool(self.version and self.download_url and self.checksum and self.source_url.startswith("https://")))

class AndroidOfficialProvider:
    ALLOWED_COMPONENTS = {"platform-tools", "build-tools", "platforms", "cmdline-tools"}
    def __init__(self, fetcher=None): self.fetcher = fetcher

    def research(self, component: str, *, version: str | None = None, architecture: str | None = None):
        if component not in self.ALLOWED_COMPONENTS or self.fetcher is None:
            return None
        payload = self.fetcher(component, version, architecture)
        if not isinstance(payload, dict): return None
        return AndroidArtifact(component, payload.get("version"), "linux", architecture,
                               payload.get("download_url"), payload.get("checksum"),
                               payload.get("source_url", "https://developer.android.com/studio"),
                               tuple(payload.get("evidence_urls", ())), payload.get("checksum_algorithm", "sha256"))
