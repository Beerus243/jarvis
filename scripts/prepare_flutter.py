#!/usr/bin/env python3
import argparse
from core.environment import EnvironmentPreparationService

parser=argparse.ArgumentParser(); parser.add_argument('--dry-run',action='store_true'); args=parser.parse_args()
report=EnvironmentPreparationService().prepare('Flutter',dry_run=True)
print('ENVIRONMENT: Flutter')
print('CURRENT STATE:',report['status'])
if report.get('sdk'):
    print('DETECTED SDK:',report['sdk'].root)
if report.get('plan'):
    print('PLAN:')
    for index,step in enumerate(report['plan'].steps,1): print(f'[{index}] {step.action_type}')
print('WITHOUT EXECUTING ANY ACTION.')
