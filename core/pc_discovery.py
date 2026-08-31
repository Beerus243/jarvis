"""Découverte en lecture seule des applications desktop installées."""
from pathlib import Path
import configparser

def discover_applications():
    result = []
    roots = (Path('/usr/share/applications'), Path.home()/'.local/share/applications')
    for root in roots:
        if not root.is_dir(): continue
        for entry in root.glob('*.desktop'):
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try: parser.read(entry, encoding='utf-8')
            except OSError: continue
            section = parser['Desktop Entry'] if parser.has_section('Desktop Entry') else None
            if not section or section.get('NoDisplay','false').lower() == 'true': continue
            name = section.get('Name')
            if name: result.append({'name': name, 'desktop_id': entry.name, 'source': str(root), 'command': section.get('Exec')})
    return result
