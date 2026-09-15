"""Commandes V6.3–6.9 explicites, partagées par la voix et le terminal."""
import re
from core.command_understanding import normalize_command
from core.vision.capture import VisionError


def handle_session_command(message):
    text = re.sub(r'^(?:hey )?jarvis ', '', normalize_command(message))
    try:
        if text in {'utilise la vision locale', 'utilise la vision locale pour cette session',
                    'utilise groq pour la vision', 'utilise la vision groq', 'desactive la vision'}:
            from core.vision.providers import switch_provider
            return switch_provider('disabled' if text == 'desactive la vision' else 'local' if 'locale' in text else 'groq')
        if text in {'verifie l etat de tes capacites', 'diagnostic des capacites', 'etat de la vision', 'statistiques de la vision'}:
            from core.vision.health import capability_report, format_report
            return format_report(capability_report())
        if text.startswith('cible ') or text.startswith('definis la zone '):
            from core.vision.targets import parse_target, select_target
            value = text.removeprefix('cible ') if text.startswith('cible ') else text.replace('definis la zone ', 'zone ', 1)
            target = parse_target(value)
            if target is None:
                return 'Précise « cible la fenêtre active », « cible le moniteur 1 » ou « définis la zone 0 0 800 600 ».'
            if target.kind == 'monitor':
                from core.vision.targets import monitor_rectangle
                monitor_rectangle(target.monitor)
            select_target(target)
            return f'Cible visuelle de session : {target.label}. Dis « regarde la cible » ou « surveille la cible ».'
        if text in {'quelle est la cible visuelle', 'statut de la cible'}:
            from core.vision.targets import selected_target
            return 'Cible visuelle : ' + selected_target().label + '.'
        # Préserver casse, accents, espaces et ponctuation du chemin utilisateur.
        match = re.fullmatch(r'(?:hey\s+)?(?:jarvis[, ]+)?diagnostique cette erreur avec le (?:fichier|journal)\s+(.+)', str(message).strip(), re.I)
        if match:
            from core.vision.development import diagnose
            return diagnose(match[1])
        if text.startswith('diagnostique cette erreur'):
            return 'Dis « diagnostique cette erreur avec le fichier », puis son chemin exact, après avoir regardé l’écran.'
        if text in {'prepare la correction et montre moi ce que tu ferais', 'prepare la correction', 'prepare une action visuelle', 'prepare la proposition visuelle'}:
            from core.vision.development import prepare_action
            return prepare_action()
        if text in {'confirme la proposition visuelle', 'execute la proposition visuelle'}:
            from core.vision.development import execute_proposal
            return execute_proposal()
        if text in {'annule la proposition visuelle', 'arrete l action visuelle'}:
            from core.vision.development import clear
            clear()
            return 'Proposition visuelle annulée.'
        minutes = {'un':1,'une':1,'deux':2,'trois':3,'quatre':4,'cinq':5,'six':6,'sept':7,'huit':8,'neuf':9,'dix':10,'onze':11,'douze':12,'treize':13,'quatorze':14,'quinze':15}
        routine_text = re.sub(r' pendant (' + '|'.join(minutes) + r') minutes?', lambda m: ' pendant ' + str(minutes[m[1]]) + ' minutes', text)
        routine = re.fullmatch(r'(?:quand je code previens moi des erreurs de compilation|active la routine de developpement)(?: pendant (\d+) minutes?)?(?: entre (\d+)\s*h et (\d+)\s*h)?', routine_text)
        if routine or text in {'liste les routines', 'statut des routines', 'desactive la routine de developpement', 'arrete les routines'}:
            from core.runtime import get_runtime
            runtime = get_runtime()
            if runtime is None:
                return 'Les routines nécessitent le runtime actif, sans --no-proactive.'
            if routine:
                duration = int(routine[1] or 15) * 60
                hours = (int(routine[2]), int(routine[3])) if routine[2] else None
                return runtime.visual_routines.start(duration=duration, hours=hours)
            if text in {'liste les routines', 'statut des routines'}:
                return runtime.visual_routines.status()
            return runtime.visual_routines.stop()
        if text.startswith(('active la routine de developpement', 'quand je code')):
            return 'Précise « active la routine de développement pendant 10 minutes », éventuellement « entre 9h et 18h ».'
    except VisionError as error:
        return str(error)
    return None
