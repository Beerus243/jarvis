#!/usr/bin/env python3
"""Manual, confirmation-gated Flutter installation smoke test.

This scaffold intentionally stops before side effects until a validated
research result and an explicit confirmation are available.
"""
from core.environment import EnvironmentPreparationService, InstallationEngine
from core.environment.installers.flutter_installer import FlutterInstaller

def main():
    service = EnvironmentPreparationService()
    report = service.prepare('Flutter', dry_run=True)
    print('Plan Flutter:', report)
    if report['status'] != 'PLANNED':
        print('Installation impossible: recherche officielle nécessaire.')
        return
    answer = input('Confirmer l’installation user-space de Flutter ? [oui/non] ').strip().lower()
    if answer not in {'oui', 'o', 'yes', 'y'}:
        print('Installation annulée.')
        return
    research = report['research']
    installer = FlutterInstaller()
    artifact = installer.artifact_from_research(research)
    if artifact is None:
        print('Artefact Flutter validé indisponible : aucune opération lancée.')
        return
    runtime = InstallationEngine()
    result = runtime.execute(installer.plan(), artifact=artifact, dry_run=False,
                             confirmation_handler=lambda step: True)
    print(result.to_dict())

if __name__ == '__main__':
    main()
