"""Official Eclipse Adoptium metadata provider (metadata only)."""
from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urlencode, urlparse
import platform

from .research import EnvironmentResearchResult, EnvironmentMetadata, OfficialSource

ADOPTIUM_SOURCE = OfficialSource(
    "Eclipse Adoptium", "adoptium.net", "https://api.adoptium.net/",
    "https://api.adoptium.net/v3/info/available_releases",
    ("api.adoptium.net", "github.com"), "https://adoptium.net/"
)

@dataclass(frozen=True)
class JDKRequest:
    feature_version: int | None = None
    platform: str = "linux"
    architecture: str = "x64"
    image_type: str = "jdk"
    release_type: str = "ga"

class AdoptiumProvider:
    def __init__(self, fetcher=None, source=ADOPTIUM_SOURCE):
        self.fetcher = fetcher
        self.source = source

    def research(self, request: JDKRequest | None = None) -> EnvironmentResearchResult:
        request = request or JDKRequest(architecture=self._architecture())
        if request.platform != "linux" or request.architecture not in {"x64", "aarch64"}:
            return EnvironmentResearchResult(official_sources=[self.source], warnings=["Plateforme ou architecture non supportée."])
        if self.fetcher is None:
            return EnvironmentResearchResult(official_sources=[self.source], warnings=["Fetcher officiel indisponible."])
        feature = str(request.feature_version) if request.feature_version else None
        if feature is None:
            try:
                releases = self.fetcher(self.source.metadata_url)
                candidates = (releases.get("available_lts_releases") or
                              releases.get("available_releases") or []) if isinstance(releases, dict) else []
                candidates = [int(value) for value in candidates if str(value).isdigit()]
                if not candidates:
                    return EnvironmentResearchResult(official_sources=[self.source], warnings=["Releases LTS Adoptium indisponibles."])
                feature = str(max(candidates))
            except Exception as exc:
                return EnvironmentResearchResult(official_sources=[self.source], warnings=[str(exc)])
        query = urlencode({"architecture": request.architecture, "image_type": request.image_type,
                           "os": request.platform, "release_type": request.release_type, "vendor": "eclipse"})
        url = f"https://api.adoptium.net/v3/assets/latest/{feature}/hotspot?{query}"
        try:
            payload = self.fetcher(url)
        except Exception as exc:
            return EnvironmentResearchResult(official_sources=[self.source], warnings=[str(exc)])
        if not isinstance(payload, list) or not payload:
            return EnvironmentResearchResult(official_sources=[self.source], warnings=["Aucun artefact officiel."])
        item = payload[0] if isinstance(payload[0], dict) else {}
        binary = item.get("binary") or {}
        package = binary.get("package") or {}
        version = (item.get("version") or {}).get("semver")
        download = package.get("link")
        checksum = package.get("checksum")
        if not all((version, download, checksum)):
            return EnvironmentResearchResult(official_sources=[self.source], warnings=["Métadonnées JDK incomplètes."])
        parsed = urlparse(download)
        if parsed.scheme != "https" or parsed.hostname not in {"api.adoptium.net", "github.com", "githubusercontent.com"}:
            return EnvironmentResearchResult(official_sources=[self.source], warnings=["URL JDK hors domaines officiels."])
        metadata = EnvironmentMetadata(str(version), "lts", "linux", "x86_64" if request.architecture == "x64" else request.architecture,
                                       package.get("name") or "temurin-jdk", download, str(checksum),
                                       source="https://adoptium.net/", verification_method="sha256")
        return EnvironmentResearchResult(official_sources=[self.source], version=str(version),
                                         artifacts=[metadata], confidence=1.0, status="READY")

    @staticmethod
    def _architecture():
        return "aarch64" if platform.machine().lower() in {"aarch64", "arm64"} else "x64"
