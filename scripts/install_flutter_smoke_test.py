#!/usr/bin/env python3
"""Manual, confirmation-gated Flutter installation smoke test.

This scaffold intentionally stops before side effects until a validated
research result and an explicit confirmation are available.
"""
from core.environment import EnvironmentPreparationService

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
    print('Aucune opération réelle n’est configurée dans ce smoke test.')

if __name__ == '__main__':
    main()
