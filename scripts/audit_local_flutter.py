#!/usr/bin/env python3
"""Read-only audit of locally downloaded Flutter archives (never networked)."""
from pathlib import Path
from core.environment.local_artifacts import LocalArtifactDiscovery

def main():
    discovery=LocalArtifactDiscovery(); candidates=discovery.discover(include_invalid=True)
    print('JARVIS LOCAL FLUTTER AUDIT\n')
    if not candidates: print('NO_LOCAL_FLUTTER_ARTIFACT'); return 0
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
