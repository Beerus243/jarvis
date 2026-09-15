"""Diagnostic sans capture, ni import GPU lourd, ni envoi de données."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

from core.state_store import get_store
from core.vision.providers import provider_name, metrics, quota

SCHEMA_VERSION = 1


def migrate():
    """Migration additive et idempotente ; aucune modification des mémoires V5."""
    store = get_store()
    def upgrade(value):
        value = value or {}
        version = value.get('schema', 0)
        if type(version) is not int or version > SCHEMA_VERSION:
            raise RuntimeError('Configuration visuelle plus récente ou invalide. Migration annulée.')
        return {**value, 'schema': SCHEMA_VERSION, 'version': '6.9'}
    return store.mutate('vision_config', 'version', upgrade)


def capability_report():
    from core.vision.targets import selected_target
    from core.vision.client import DEFAULT_VISION_MODEL
    modules = {name: importlib.util.find_spec(name) is not None for name in ('numpy', 'openai', 'pyaudio', 'kokoro', 'openwakeword')}
    tools = {name: bool(shutil.which(name)) for name in ('ffmpeg', 'ffprobe', 'spectacle', 'kscreen-doctor', 'jarvis-kwin-context', 'ollama')}
    from core.kwin_context import get_active_window
    window = get_active_window()
    window_tracking = bool(window.get('available') and window.get('id'))
    return {'window_tracking': window_tracking, 'version': '6.9', 'python': sys.executable, 'session': os.getenv('XDG_SESSION_TYPE', 'unknown'),
            'provider': provider_name(), 'groq_key_configured': bool(os.getenv('GROQ_API_KEY')),
            'groq_model': os.getenv('JARVIS_VISION_MODEL', DEFAULT_VISION_MODEL),
            'local_model': os.getenv('JARVIS_LOCAL_VISION_MODEL') or None,
            'local_status': 'à vérifier' if os.getenv('JARVIS_LOCAL_VISION_MODEL') else 'non configuré',
            'camera_present': Path(os.getenv('JARVIS_CAMERA_DEVICE', '/dev/video0')).exists(),
            'target': selected_target().label, 'hourly_limit': quota(), 'metrics': metrics(),
            'modules': modules, 'tools': tools,
            'live_checks_pending': ['micro et interruption Hey Jarvis', 'lecture visuelle réelle',
                                    'surveillance sur le bureau', 'sélection vidéo et finalisation',
                                    'inférence locale sur le GPU']}


def hardware_report():
    """Mesure facultative du matériel uniquement ; aucun chargement de modèle."""
    if not shutil.which('nvidia-smi'):
        return {'gpu': 'nvidia-smi indisponible'}
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.free,driver_version',
                                 '--format=csv,noheader'], capture_output=True, text=True, timeout=5, check=True)
        return {'gpu': result.stdout.strip(), 'local_inference': 'non mesurée'}
    except (OSError, subprocess.SubprocessError):
        return {'gpu': 'GPU inaccessible dans cet environnement', 'local_inference': 'non mesurée'}


def format_report(report):
    missing = [name for name, available in {**report['modules'], **report['tools']}.items()
               if not available and name not in {'ollama', 'jarvis-kwin-context'}]
    observations = [f"Jarvis V{report['version']}. Vision : {report['provider']}. Cible : {report['target']}.",
        f"Budget : {report['hourly_limit']} analyses par heure dans cette session. Vision locale : {report['local_status']}."]
    if missing:
        observations.append('Composants absents : ' + ', '.join(missing) + '.')
    if not report['window_tracking']:
        observations.append('Suivi de fenêtre précise indisponible sans contexte KWin ; fenêtre active ponctuelle et zones disponibles.')
    if report['provider'] == 'groq' and not report['groq_key_configured']:
        observations.append('Clé Groq absente de cet environnement.')
    for provider, stats in report['metrics'].items():
        observations.append(f"{provider} : {stats['calls']} appels, {stats['errors']} erreurs, dernier appel {stats['last_seconds']} secondes.")
    observations.append('Ce diagnostic ne teste pas le micro et ne prend aucune image.')
    return '\n'.join(observations)
