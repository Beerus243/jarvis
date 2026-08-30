"""Official Eclipse Adoptium metadata provider (metadata only)."""
from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urlencode, urlparse
import platform

from .research import EnvironmentResearchResult, EnvironmentMetadata, OfficialSource
from .research import MetadataCache
from .metadata_cache import inspect_cached_metadata, CachePolicy

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
    def __init__(self, fetcher=None, source=ADOPTIUM_SOURCE, cache=None):
        self.fetcher = fetcher
        self.source = source
        self.cache = cache

    def research(self, request: JDKRequest | None = None) -> EnvironmentResearchResult:
        request = request or JDKRequest(architecture=self._architecture())
        if request.platform != "linux" or request.architecture not in {"x64", "aarch64"}:
            return EnvironmentResearchResult(official_sources=[self.source], warnings=["Plateforme ou architecture non supportée."])
        if self.fetcher is None:
            cached = self._cached(request)
            if cached is not None:
                return cached
            return EnvironmentResearchResult(official_sources=[self.source], warnings=["Fetcher officiel indisponible."], provider_state="NETWORK_UNAVAILABLE")
        cached = self._cached(request)
        if cached is not None:
            return cached
        feature = str(request.feature_version) if request.feature_version else None
        if feature is None:
            try:
                releases = self._fetch(self.source.metadata_url)
                candidates = (releases.get("available_lts_releases") or
                              releases.get("available_releases") or []) if isinstance(releases, dict) else []
                candidates = [int(value) for value in candidates if str(value).isdigit()]
                if not candidates:
                    return EnvironmentResearchResult(official_sources=[self.source], warnings=["Releases LTS Adoptium indisponibles."], provider_state="INVALID_RESPONSE")
                feature = str(max(candidates))
            except Exception as exc:
                state = "INVALID_RESPONSE" if isinstance(exc, (ValueError, KeyError, TypeError)) else "NETWORK_UNAVAILABLE"
                return EnvironmentResearchResult(official_sources=[self.source], warnings=[str(exc)], provider_state=state)
        query = urlencode({"architecture": request.architecture, "image_type": request.image_type,
                           "os": request.platform, "release_type": request.release_type, "vendor": "eclipse"})
        url = f"https://api.adoptium.net/v3/assets/latest/{feature}/hotspot?{query}"
        try:
            payload = self._fetch(url)
        except Exception as exc:
            state = "INVALID_RESPONSE" if isinstance(exc, (ValueError, KeyError, TypeError)) else "NETWORK_UNAVAILABLE"
            return EnvironmentResearchResult(official_sources=[self.source], warnings=[str(exc)], provider_state=state)
        if not isinstance(payload, list) or not payload:
            return EnvironmentResearchResult(official_sources=[self.source], warnings=["Aucun artefact officiel."], provider_state="NOT_AVAILABLE")
        item = payload[0] if isinstance(payload[0], dict) else {}
        binary = item.get("binary") or {}
        package = binary.get("package") or {}
        version = (item.get("version") or {}).get("semver")
        download = package.get("link")
        checksum = package.get("checksum")
        if not all((version, download, checksum)):
            return EnvironmentResearchResult(official_sources=[self.source], warnings=["Métadonnées JDK incomplètes."], provider_state="INVALID_ARTIFACT")
        parsed = urlparse(download)
        if parsed.scheme != "https" or parsed.hostname not in {"api.adoptium.net", "github.com", "githubusercontent.com"}:
            return EnvironmentResearchResult(official_sources=[self.source], warnings=["URL JDK hors domaines officiels."], provider_state="INVALID_ARTIFACT")
        metadata = EnvironmentMetadata(str(version), "lts", "linux", "x86_64" if request.architecture == "x64" else request.architecture,
                                       package.get("name") or "temurin-jdk", download, str(checksum),
                                       source="https://adoptium.net/", verification_method="sha256")
        return EnvironmentResearchResult(official_sources=[self.source], version=str(version),
                                         artifacts=[metadata], confidence=1.0, status="READY", provider_state="AVAILABLE")

    def _fetch(self, url):
        last = None
        for _ in range(2):
            try:
                value = self.fetcher(url)
                if not isinstance(value, (dict, list)):
                    raise ValueError("Réponse JSON invalide.")
                return value
            except Exception as exc:
                last = exc
        raise last

    def _cached(self, request):
        if self.cache is None:
            return None
        key = f"adoptium-jdk-{request.platform}-{request.architecture}"
        payload = self.cache.load_official(key)
        if payload is None:
            return None
        policy, data = inspect_cached_metadata(payload, provider="Eclipse Adoptium",
            allowed_hosts={"api.adoptium.net", "adoptium.net", "github.com", "githubusercontent.com"},
            architecture="x86_64" if request.architecture == "x64" else request.architecture)
        if policy != CachePolicy.FRESH_CACHE:
            return None
        try:
            item = EnvironmentMetadata(**data)
        except (TypeError, ValueError):
            return EnvironmentResearchResult(official_sources=[self.source], warnings=["Cache Adoptium incohérent."], provider_state="INVALID_ARTIFACT")
        return EnvironmentResearchResult(official_sources=[self.source], version=item.version,
            artifacts=[item], confidence=0.9, status="READY", provider_state="CACHED_OFFICIAL_METADATA")

    @staticmethod
    def _architecture():
        return "aarch64" if platform.machine().lower() in {"aarch64", "arm64"} else "x64"
