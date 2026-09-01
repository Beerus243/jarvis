"""Découverte en lecture seule des applications desktop installées."""
from pathlib import Path
import configparser
import logging

APPLICATION_ROOTS = (Path('/usr/share/applications'), Path.home()/'.local/share/applications', Path('/var/lib/flatpak/exports/share/applications'), Path.home()/'.local/share/flatpak/exports/share/applications')

def discover_applications():
    result = []
    roots = APPLICATION_ROOTS
    for root in roots:
        if not root.is_dir(): continue
        for entry in root.glob('*.desktop'):
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try: parser.read(entry, encoding='utf-8')
            except OSError: continue
            section = parser['Desktop Entry'] if parser.has_section('Desktop Entry') else None
            if not section or section.get('NoDisplay','false').lower() == 'true': continue
            name = section.get('Name')
            if name:
                item = {'name': name, 'desktop_id': entry.name, 'source': str(root), 'command': section.get('Exec')}
                result.append(item)
                if 'flatpak' in str(root): logging.info('Application Flatpak trouvée: %s', name)
    return result
