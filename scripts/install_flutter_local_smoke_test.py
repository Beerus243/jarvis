#!/usr/bin/env python3
"""Install a previously downloaded Flutter archive, only after confirmation."""
import sys
from pathlib import Path
from core.environment import LocalArtifactDiscovery, InstallationEngine
from core.environment.installers.flutter_installer import FlutterInstaller

def main():
    explicit=Path(sys.argv[1]).expanduser() if len(sys.argv)>1 else None
    discovery=LocalArtifactDiscovery()
    candidates=[discovery.inspect(explicit)] if explicit else discovery.discover(architecture='x86_64')
    candidates=[c for c in candidates if c.validation_status=='VALID' and c.version]
    if not candidates: print('NO_LOCAL_FLUTTER_ARTIFACT'); return 2
    candidate=candidates[0]; version=candidate.version
    installer=FlutterInstaller(); status=installer.inspect_installation(version)['status']
    if status=='READY': print('ALREADY_READY'); return 0
    destination=Path.home()/'.local/share/jarvis/environments/flutter'/version
    artifact=discovery.to_installation_artifact(candidate,destination)
    print(f'Flutter local trouvé: {candidate.path}\nVersion: {version}\nArchitecture: {candidate.architecture}\nSHA-256 local: {artifact.checksum}\nTrust: LOCAL_UNVERIFIED\nDestination: {destination}\nPATH: {destination}/bin')
    if input('Continuer ? [oui/non] ').strip().lower() not in {'oui','o','yes','y'}: print('CANCELLED'); return 0
    report=InstallationEngine().execute(installer.plan(),artifact=artifact,dry_run=False,confirmation_handler=lambda _:True)
    print(report.to_dict()); return 0 if report.to_dict()['success'] else 1

if __name__=='__main__': raise SystemExit(main())
