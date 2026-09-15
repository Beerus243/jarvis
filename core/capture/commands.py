"""Grammaire fermée des captures : aucune exécution depuis une phrase descriptive."""
import re
from core.command_understanding import normalize_command

NUMBERS = {'un': 1, 'une': 1, 'deux': 2, 'trois': 3, 'quatre': 4, 'cinq': 5,
           'dix': 10, 'quinze': 15, 'vingt': 20, 'trente': 30, 'soixante': 60}
TARGET = r"(?P<target>(?:mon |l |cet |le )?ecran|(?:la |ma |cette )?fenetre(?: active)?|(?:une |la |cette )?zone(?: de (?:l |mon )?ecran)?)"


def parse_capture_command(message):
    if re.search(r'pendant\s+-\s*\d', str(message), re.I):
        return None
    text = re.sub(r'^(?:hey )?jarvis ', '', normalize_command(message))
    text = re.sub(r' s il te plait$', '', text)
    if text in {'arrete la video', 'arrete l enregistrement', 'arrete la capture video',
                'stoppe la video', 'stoppe l enregistrement', 'termine l enregistrement'}:
        return {'action': 'RECORDING_STOP'}
    if text in {'statut de la video', 'statut de l enregistrement', 'etat de l enregistrement',
                'est ce que tu enregistres', 'enregistres tu l ecran'}:
        return {'action': 'RECORDING_STATUS'}
    photo = re.fullmatch(r'(?:capture |(?:fais|prends) une capture (?:d |de )?)' + TARGET, text)
    if text in {'screenshot', 'capture ecran', 'fais une capture ecran', 'prends une capture ecran'}:
        return 'SCREENSHOT'
    if photo:
        target = photo['target']
        scope = 'window' if 'fenetre' in target else 'region' if 'zone' in target else 'screen'
        return 'SCREENSHOT' if scope == 'screen' else {'action': 'SCREENSHOT', 'scope': scope}
    video = re.fullmatch(
        r'(?:(?:enregistre|filme) |(?:fais|prends|demarre|lance) (?:une |la )?(?:capture video|video|enregistrement)(?: de | d | ))'
        + TARGET + r'(?: pendant (?P<number>\d+|' + '|'.join(NUMBERS) + r') (?P<unit>secondes?|minutes?))?', text)
    if text in {'demarre l enregistrement', 'demarre une capture video', 'fais une capture video'}:
        return {'action': 'RECORDING_START', 'scope': 'screen', 'duration': 60}
    if video:
        target, amount = video['target'], video['number']
        duration = (int(amount) if amount and amount.isdigit() else NUMBERS.get(amount, 60))
        if video['unit'] and video['unit'].startswith('minute'):
            duration *= 60
        return {'action': 'RECORDING_START', 'scope': 'window' if 'fenetre' in target else 'region' if 'zone' in target else 'screen', 'duration': duration}
    return None
