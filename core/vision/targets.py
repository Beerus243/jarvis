"""Cibles en mémoire ; coordonnées en pixels de la capture du bureau."""
from dataclasses import dataclass, replace
import json
import re
import struct
import subprocess
import threading

from core.vision.capture import VisionError


@dataclass(frozen=True)
class VisualTarget:
    kind: str = 'screen'
    rect: tuple | None = None  # x, y, largeur, hauteur, avant redimensionnement
    monitor: int | None = None
    window_id: str | None = None

    def __post_init__(self):
        if self.kind not in {'screen', 'window', 'region', 'monitor'}:
            raise VisionError('Cible visuelle inconnue.')
        if self.rect is not None and (len(self.rect) != 4 or any(type(v) is not int for v in self.rect)
                or min(self.rect[:2]) < 0 or min(self.rect[2:]) < 16 or max(self.rect) > 32768):
            raise VisionError('Zone invalide : x et y positifs, largeur et hauteur de 16 à 32768 pixels.')
        if self.kind == 'monitor' and (type(self.monitor) is not int or self.monitor < 1):
            raise VisionError('Numéro de moniteur invalide.')

    @property
    def label(self):
        if self.kind == 'region':
            return 'la zone ' + (', '.join(map(str, self.rect)) if self.rect else 'sélectionnée à la souris')
        if self.kind == 'monitor':
            return f'le moniteur {self.monitor}'
        return 'la fenêtre active' if self.kind == 'window' else 'l’écran'


def monitor_rectangle(number):
    try:
        result = subprocess.run(['kscreen-doctor', '-j'], capture_output=True, text=True, timeout=3, check=True)
        config = json.loads(result.stdout)
        outputs = [o for o in config['outputs'] if o.get('enabled') and o.get('connected')]
        output = next(o for o in outputs if o['id'] == number)
        # Refuser les topologies ambiguës plutôt que transmettre le mauvais écran.
        if any(o.get('scale', 1) != 1 or o.get('rotation', 1) != 1 for o in outputs):
            raise VisionError('Ciblage par moniteur indisponible avec rotation ou mise à l’échelle. Utilise une zone en pixels.')
        x0, y0 = min(o['pos']['x'] for o in outputs), min(o['pos']['y'] for o in outputs)
        return (output['pos']['x'] - x0, output['pos']['y'] - y0,
                output['size']['width'], output['size']['height'])
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, StopIteration, TypeError):
        raise VisionError('Moniteur inaccessible. Vérifie son numéro avec kscreen-doctor -o.') from None


def pin_window(target):
    from core.kwin_context import get_active_window
    window = get_active_window()
    identity = window.get('id')
    if not window.get('available') or identity is None or str(identity) in {'', 'undefined', 'null', 'None'}:
        raise VisionError('Le suivi d’une fenêtre nécessite un instantané KWin avec identifiant. Utilise une zone fixe, ou une analyse ponctuelle de la fenêtre active.')
    return replace(target, window_id=str(identity))


def check_window(target):
    if target.window_id is None:
        return
    from core.kwin_context import get_active_window
    window = get_active_window()
    if not window.get('available') or str(window.get('id')) != target.window_id:
        raise VisionError('La fenêtre ciblée n’est plus active. Capture écartée, sans changement de cible.')


def crop_filter(target, png_path):
    rect = monitor_rectangle(target.monitor) if target.kind == 'monitor' else target.rect
    if rect is None:
        return ''
    with open(png_path, 'rb') as image:
        header = image.read(24)
    if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n':
        raise VisionError('Dimensions de la capture illisibles.')
    width, height = struct.unpack('>II', header[16:24])
    x, y, w, h = rect
    if x < 0 or y < 0 or w < 16 or h < 16 or x + w > width or y + h > height:
        raise VisionError('La zone dépasse les dimensions de l’écran. Redéfinis la cible.')
    return f'crop={w}:{h}:{x}:{y}:exact=1,'


_lock = threading.Lock()
_selected = VisualTarget()


def selected_target():
    with _lock:
        return _selected


def select_target(target):
    global _selected
    with _lock:
        _selected = target


def parse_target(text):
    if text in {'mon ecran', 'l ecran', 'tout l ecran', 'ecran'}:
        return VisualTarget()
    if text in {'la fenetre active', 'cette fenetre', 'ce terminal', 'seulement ce terminal'}:
        return VisualTarget('window')
    if text in {'une zone', 'une zone de l ecran'}:
        return VisualTarget('region')
    if text in {'cette zone', 'la cible', 'la cible visuelle'}:
        return selected_target()
    match = re.fullmatch(r'(?:le )?moniteur (\d+)', text)
    if match:
        return VisualTarget('monitor', monitor=int(match[1]))
    match = re.fullmatch(r'(?:la )?zone (\d+) (\d+) (\d+) (\d+)', text)
    if match:
        return VisualTarget('region', rect=tuple(map(int, match.groups())))
    return None
