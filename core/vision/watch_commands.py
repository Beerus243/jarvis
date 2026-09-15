"""Commandes explicites de surveillance, indépendantes du dialogue libre."""
import re

from core.command_understanding import normalize_command
from core.vision.capture import VisionError

MINUTES = {'une': 1, 'un': 1, 'deux': 2, 'trois': 3, 'cinq': 5, 'dix': 10, 'quinze': 15}


def handle_watch_command(message):
    text = re.sub(r'^(?:hey )?jarvis ', '', normalize_command(message))
    stop = text in {'arrete la surveillance', 'arrete la surveillance visuelle', 'stoppe la surveillance',
                    'arrete de surveiller', 'arrete de surveiller l ecran', 'stop surveillance'}
    status = text in {'statut de la surveillance', 'etat de la surveillance', 'que surveilles tu', 'quelle surveillance est active'}
    duration = 300
    suffix = re.search(r' pendant (\d+|une|un|deux|trois|cinq|dix|quinze) minutes?$', text)
    if suffix:
        n = suffix[1]
        duration = (int(n) if n.isdigit() else MINUTES[n]) * 60
        text = text[:suffix.start()]
    from core.vision.targets import parse_target, selected_target
    target = None
    scoped = re.search(r' sur (.+)$', text)
    if scoped:
        target = parse_target(scoped[1])
        if target:
            text = text[:scoped.start()]
    if text in {'surveille seulement ce terminal', 'surveille cette zone', 'surveille la cible', 'surveille la fenetre active'}:
        target = parse_target(text.removeprefix('surveille '))
        text = 'surveille les erreurs'
    goals = {
        'compilation': (r'surveille (?:cette|la|ma) compilation(?: et previens moi quand elle (?:termine|se termine|est terminee))?',),
        'download': (r'surveille (?:ce|le|mon) telechargement(?: et previens moi quand il (?:termine|se termine|est termine))?',
                     r'previens moi quand (?:ce|le|mon) telechargement est termine'),
        'error': (r'surveille (?:l apparition d une erreur|les erreurs)(?: a l ecran)?',
                  r'previens moi si une erreur apparait (?:a l ecran|sur mon ecran)'),
    }
    goal = next((goal for goal, patterns in goals.items() if any(re.fullmatch(p, text) for p in patterns)), None)
    if not (goal or stop or status):
        if (text.startswith('surveille ') or re.match(r'previens moi (?:si une erreur|quand (?:ce|le|mon) telechargement)', text)):
            return 'Précise : « surveille cette compilation », « surveille ce téléchargement » ou « préviens-moi si une erreur apparaît à l’écran », pendant 1 à 15 minutes.'
        return None
    from core.runtime import get_runtime
    runtime = get_runtime()
    if runtime is None:
        return 'La surveillance visuelle nécessite le runtime actif. Relance Jarvis sans --no-proactive.' if goal else 'Aucune surveillance visuelle active.'
    if stop:
        return runtime.visual_watch.stop()
    if status:
        return runtime.visual_watch.status()
    if not 60 <= duration <= 900:
        return 'Choisis une surveillance de 1 à 15 minutes.'
    from core.vision.service import _vision_enabled
    from core.vision.client import GroqVisionClient
    if not _vision_enabled():
        return 'La vision est désactivée. Aucune surveillance démarrée.'
    try:
        from core.vision.providers import get_client
        get_client(groq_factory=GroqVisionClient)  # Précontrôle avant capture.
    except VisionError as error:
        return str(error)
    try:
        target = target or selected_target()
        options = {'target': target} if target.kind != 'screen' else {}
        return runtime.visual_watch.start(goal, duration=duration, **options)
    except VisionError as error:
        return str(error)
