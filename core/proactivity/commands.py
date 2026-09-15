"""Commandes personnelles locales, avant les réponses libres du LLM."""
import re
from datetime import datetime
from core.command_understanding import normalize_command
from core.state_store import get_store
from core.proactivity import model, projects


def handle_personal_command(message):
    from core.runtime import get_runtime
    runtime = get_runtime()
    agent = getattr(runtime, 'personal_agent', None)
    text = normalize_command(message)
    text = {'pourquoi tu me proposes ca': 'pourquoi cette proposition',
            'non ce n est pas mon habitude': 'oublie mon rythme de pause'}.get(text, text)
    if agent:
        agent.touch()
    if agent and re.fullmatch(r'\d+ minutes?', text):
        with agent.lock:
            if agent.pending() and agent.offer['kind'] == 'preference' and agent.offer['state'] == 'DELIVERED':
                text = 'ma pause apres ' + text
    match = re.fullmatch(r'(?:ma pause apres|je veux une pause (?:apres|toutes les)|propose moi une pause (?:apres|toutes les)) (\d+) minutes?', text)
    if match:
        try:
            model.confirm('break_minutes', int(match[1]))
        except ValueError as error:
            return str(error)
        if agent:
            with agent.lock:
                agent._finish('DONE')
        return model.describe()
    if text in {'mes habitudes', 'que sais tu de mes habitudes', 'mon rythme de pause'}:
        return model.describe()
    if text in {'oublie mon rythme de pause', 'oublie mes habitudes de pause'}:
        model.forget_break()
        if agent:
            with agent.lock:
                agent._finish('CANCELLED')
                agent.offer = None
                get_store().delete('v7', 'offer')
        return 'Rythme, hypothèses et observations de pause oubliés. Leur apprentissage est suspendu jusqu’à une nouvelle préférence explicite.'
    preferences = {
        'ajoute la musique a ma routine de pause': ('pause_music', True),
        'retire la musique de ma routine de pause': ('pause_music', False),
        'ne me propose plus de pause': ('break_proposals', False),
        'propose moi a nouveau des pauses': ('break_proposals', True),
        'ne me pose plus de questions': ('questions', False),
        'pose moi a nouveau des questions': ('questions', True),
        'pose moi moins de questions': ('question_limit', 1),
        'laisse passer les rappels pendant mon sommeil': ('sleep_reminders', True),
        'aucun rappel pendant mon sommeil': ('sleep_reminders', False),
    }
    if text in preferences:
        key, value = preferences[text]
        model.confirm(key, value)
        if agent and value is False and key in {'questions', 'break_proposals'}:
            with agent.lock:
                if agent.offer and agent.offer['kind'] == ('preference' if key == 'questions' else 'break'):
                    agent._finish('CANCELLED')
        return 'Préférence enregistrée.'
    modes = {'je vais dormir': 'sleeping', 'bonne nuit jarvis': 'sleeping',
             'je suis reveille': 'auto', 'je reprends le travail': 'auto',
             'je fais une pause': 'break', 'mode concentration': 'focus',
             'fin du mode concentration': 'auto'}
    specific = text in modes or text in {'mon contexte de travail', 'ma session de travail', 'prepare ma pause',
        'confirme ma proposition', 'refuse ma proposition', 'pas de proposition aujourd hui',
        'pourquoi cette proposition', 'mon point de reprise', 'reprends mon projet', 'ouvre mon projet de reprise'} or text.startswith('reporte ma proposition')
    declared = re.fullmatch(r'je travaille sur (.+)', text)
    if not agent:
        return 'Le suivi personnel nécessite Jarvis lancé avec la proactivité activée.' if specific or declared else None
    if declared:
        project = projects.find_project(declared[1])
        if not project:
            return 'Ce projet n’est pas enregistré ou son nom est ambigu. Enregistre son chemin dans les projets Jarvis.'
        get_store().put('v7', 'declared_project', project['key'])
        model.event('project_declared', {'project': project['key']})
        return f"Projet déclaré : {project['name']}. Le temps sera compté lorsque son outil de développement sera actif."
    if text in modes:
        agent.set_mode(modes[text])
        if modes[text] in {'sleeping', 'break'}:
            runtime.visual_routines.stop()
            runtime.visual_watch.stop()
        return {'sleeping': 'Bonne nuit Fabrice. Je suspends mes interventions jusqu’à « je suis réveillé ».',
                'auto': 'Je reprends le suivi et les propositions selon ta présence.',
                'break': 'Bonne pause. Dis « je reprends le travail » à ton retour.',
                'focus': 'Concentration activée : les rappels restent disponibles, les propositions attendront.'}[modes[text]]
    if text in {'mon contexte de travail', 'ma session de travail'}:
        return agent.status()
    if text == 'prepare ma pause':
        return agent.propose()
    if text == 'confirme ma proposition':
        return agent.feedback('accept')
    if text == 'refuse ma proposition':
        return agent.feedback('refuse')
    match = re.fullmatch(r'reporte ma proposition(?: de| dans)? (\d+) minutes?', text)
    if match:
        return agent.feedback('defer', int(match[1]))
    if text == 'pas de proposition aujourd hui':
        get_store().put('v7', 'suppressed_day', datetime.fromtimestamp(agent.clock()).date().isoformat())
        with agent.lock:
            agent._finish('CANCELLED')
        return 'Propositions personnelles suspendues pour aujourd’hui.'
    if text == 'pourquoi cette proposition':
        with agent.lock:
            return ('Cette proposition repose sur : ' + agent.offer['reason'] + '. ' + agent.offer['message']) if agent.pending() else 'Aucune proposition en attente.'
    if text in {'mon point de reprise', 'reprends mon projet', 'ouvre mon projet de reprise'}:
        points = get_store().items('v7_checkpoints')
        if not points:
            return 'Aucun point de reprise enregistré.'
        point = max((p for _, p in points), key=lambda p: p['at'])
        # Resume the declared session; opening apps remains an explicit existing PC command.
        project = projects.find_project(point['project']['key'])
        if not project or project['path'] != point['project']['path']:
            return 'Le projet du point de reprise a changé. Vérifie son chemin enregistré.'
        if text == 'ouvre mon projet de reprise':
            from pathlib import Path
            if not Path(project['path']).is_dir():
                return 'Le dossier du projet est indisponible.'
            from core.action_executor import execute_action
            result = execute_action({'action': 'OPEN_VSCODE', 'target': project['path']})
            return result.message
        if text == 'reprends mon projet':
            get_store().put('v7', 'declared_project', project['key'])
            agent.set_mode('auto')
        tasks = '; '.join(t['goal'] for t in point['tasks'][:3]) or 'aucune tâche en cours au moment du point'
        return f"Reprise de {project['name']} : {tasks}. Les fichiers de l’éditeur ne font pas partie de ce point."
    # A bare yes must never execute another subsystem's older confirmation.
    if text in {'oui', 'ok', 'confirme', 'non', 'stop', 'arrete'}:
        with agent.lock:
            if agent.pending():
                return 'Pour la proposition personnelle, dis « confirme ma proposition » ou « refuse ma proposition ».'
    return None
