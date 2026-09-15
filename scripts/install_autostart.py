"""Installer explicitement le service utilisateur ; aperçu par défaut, aucun démarrage."""
import argparse
import configparser
from datetime import datetime
import os
from pathlib import Path
import subprocess
import tempfile

MARKER = '# Jarvis managed user service V7'


def quoted(path):
    value = str(path)
    if any(c in value for c in '\n\r\x00'):
        raise ValueError('Chemin invalide.')
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'


def render(root):
    root = Path(root).resolve()
    return f'''{MARKER}
[Unit]
Description=Jarvis personnel — voix et contexte local
PartOf=graphical-session.target
After=graphical-session-pre.target
StartLimitIntervalSec=300
StartLimitBurst=3

[Service]
Type=simple
WorkingDirectory={str(root).replace('%', '%%')}
ExecStart={quoted(root / '.venv-kokoro-cuda/bin/python')} {quoted(root / 'main.py')} --background
Environment=PYTHONUNBUFFERED=1
Restart=on-failure
RestartSec=30
TimeoutStopSec=150
UMask=0077

[Install]
WantedBy=graphical-session.target
'''


def legacy_unit(unit, root):
    """Only migrate the known old launcher, preserving other services untouched."""
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    try:
        parser.read_string(unit)
        if set(parser.sections()) != {'Unit', 'Service', 'Install'}:
            return False
        allowed = {'Unit': {'Description', 'After', 'Wants'},
                   'Service': {'Type', 'WorkingDirectory', 'ExecStart', 'Restart', 'RestartSec', 'Environment'},
                   'Install': {'WantedBy'}}
        if any(set(parser[section]) - allowed[section] for section in allowed):
            return False
        roots = {str(root), '%h/dev/jarvis'}
        return (parser['Service'].get('WorkingDirectory') in roots
                and parser['Service'].get('ExecStart') in {
                    f'{base}/.venv-kokoro-cuda/bin/python {base}/main.py --voice' for base in roots}
                and parser['Service'].get('Environment', 'PYTHONUNBUFFERED=1') == 'PYTHONUNBUFFERED=1'
                and parser['Service'].get('Type', 'simple') == 'simple'
                and parser['Install'].get('WantedBy') in {'default.target', 'graphical-session.target'})
    except configparser.Error:
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--install', action='store_true')
    modes.add_argument('--disable', action='store_true')
    parser.add_argument('--migrate-existing', action='store_true', help='Sauvegarder et migrer uniquement l’ancien lanceur Jarvis reconnu.')
    args = parser.parse_args(argv)
    if args.migrate_existing and not args.install:
        parser.error('--migrate-existing nécessite --install')
    root = Path(__file__).resolve().parents[1]
    destination = Path.home() / '.config/systemd/user/jarvis.service'
    unit = render(root)
    if not args.install and not args.disable:
        print(unit)
        print(f'# Destination : {destination}. --install active uniquement la prochaine session.')
        return 0
    old_unit = destination.read_text() if destination.exists() else None
    migrating = bool(old_unit and not old_unit.startswith(MARKER))
    if migrating and not (args.migrate_existing and legacy_unit(old_unit, root)):
        raise RuntimeError('Un service Jarvis non géré existe déjà ; il a été conservé. --install --migrate-existing permet de migrer un ancien lanceur reconnu.')
    if args.disable:
        subprocess.run(['systemctl', '--user', 'disable', '--now', 'jarvis.service'], check=True, timeout=170)
        return 0
    if not (root / '.venv-kokoro-cuda/bin/python').is_file():
        raise RuntimeError('Environnement Kokoro introuvable.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        draft = Path(directory) / 'jarvis.service'
        draft.write_text(unit)
        subprocess.run(['systemd-analyze', '--user', 'verify', str(draft)], check=True, timeout=30)
    if migrating:
        backup = destination.with_name('jarvis.service.pre-v7-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        with backup.open('x') as handle:
            handle.write(old_unit)
        print(f'Ancien service sauvegardé : {backup}')
        subprocess.run(['systemctl', '--user', 'disable', 'jarvis.service'], check=True, timeout=30)
    fd, temp = tempfile.mkstemp(prefix='.jarvis-', dir=destination.parent)
    try:
        with os.fdopen(fd, 'w') as handle:
            handle.write(unit)
        os.replace(temp, destination)
    finally:
        if Path(temp).exists():
            Path(temp).unlink()
    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True, timeout=30)
    subprocess.run(['systemctl', '--user', 'enable', 'jarvis.service'], check=True, timeout=30)
    print('Service activé pour la prochaine connexion graphique. Aucun lancement effectué maintenant.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
