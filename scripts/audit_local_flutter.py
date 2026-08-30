#!/usr/bin/env python3
"""Read-only audit of locally downloaded Flutter archives (never networked)."""
from pathlib import Path
import sys

# Lors d'une exécution directe, Python ajoute ``scripts/`` à sys.path.
# Ajouter la racine calculée permet d'importer ``core`` sans PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.environment.local_artifacts import LocalArtifactDiscovery
from core.environment.local_sdks import LocalSDKDiscovery

def main():
    discovery=LocalArtifactDiscovery(); candidates=discovery.discover(include_invalid=True)
    sdks=LocalSDKDiscovery().discover()
    print('JARVIS LOCAL FLUTTER AUDIT\n')
    if sdks:
        print('EXTRACTED SDK CANDIDATES')
        for i,sdk in enumerate(sdks,1): print(f'Candidate #{i}\nRoot: {sdk.root}\nSDK: VALID\nFlutter: {"DETECTED" if sdk.flutter else "MISSING"}\nDart: {"DETECTED" if sdk.dart else "MISSING"}\nVersion: {sdk.version or "UNKNOWN"}\nPATH: {"CONFIGURED" if sdk.path_configured else "NOT_CONFIGURED"}\nArchitecture: {sdk.architecture or "UNKNOWN"}\nState: {sdk.state}\nTrust: {sdk.trust}')
    if not candidates: return 0 if sdks else (print('NO_LOCAL_FLUTTER_ARTIFACT') or 0)
    print(f'Candidates found: {len(candidates)}')
    for index,candidate in enumerate(candidates,1):
        print(f'\nCandidate #{index}\nPath: {candidate.path}\nFormat: {candidate.format}\nSize: {candidate.size}')
        print(f'Flutter: {"VALID" if candidate.validation_status=="VALID" else "INVALID"}\nDart: {"VALID" if candidate.validation_status=="VALID" else "INVALID"}')
        print(f'Version: {candidate.version or "UNKNOWN"}\nArchitecture: {candidate.architecture or "UNKNOWN"}')
        print(f'SHA-256: {discovery.checksum(candidate.path) if candidate.path.exists() else "UNKNOWN"}\nTrust: {candidate.checksum_status}')
        compatible = candidate.validation_status=='VALID' and candidate.architecture in (None,'x86_64') and bool(candidate.version)
        print(f'Compatibility: {"COMPATIBLE" if compatible else "INCOMPATIBLE"}')
        print(f'Recommendation: {"READY_FOR_LOCAL_INSTALLATION" if compatible else candidate.reason or "VERSION_UNKNOWN"}')
    return 0
if __name__=='__main__': raise SystemExit(main())
