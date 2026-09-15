"""Captures privées, ponctuelles et bornées avec les outils Linux existants."""
from contextlib import contextmanager
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from core.actions.screenshot import ScreenCapture

MAX_IMAGE_BYTES = 4 * 1024 * 1024
SCALE = "scale=w='min(1920,iw)':h='min(1920,ih)':force_original_aspect_ratio=decrease"


class VisionError(RuntimeError):
    """Message opérationnel pouvant être lu sans détails techniques sensibles."""


@contextmanager
def capture_image(source, *, camera_device='/dev/video0'):
    if source not in {'screen', 'webcam'}:
        raise VisionError('Source visuelle inconnue. Précise écran ou webcam.')
    if not shutil.which('ffmpeg'):
        raise VisionError('La vision nécessite FFmpeg, qui est indisponible.')
    if source == 'webcam' and not re.fullmatch(r'/dev/video\d+', camera_device):
        raise VisionError('Le périphérique webcam configuré est invalide.')

    # Un répertoire unique évite de réutiliser une ancienne capture et se
    # nettoie aussi lors d'un échec réseau ou d'une interruption clavier.
    with tempfile.TemporaryDirectory(prefix='jarvis-vision-') as directory:
        output = Path(directory) / 'image.jpg'
        if source == 'screen':
            result = ScreenCapture(destination=directory, timeout=20).capture()
            if not result.success or not result.artifact_path:
                raise VisionError('Je ne peux pas capturer ton écran. Vérifie Spectacle et la session graphique.')
            input_args = ['-i', result.artifact_path]
        else:
            if not Path(camera_device).exists():
                raise VisionError('Aucune webcam disponible sur le périphérique configuré.')
            input_args = ['-f', 'video4linux2', '-i', camera_device, '-ss', '0.5']
        try:
            result = subprocess.run(
                ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                 *input_args, '-frames:v', '1', '-vf', SCALE, '-q:v', '3',
                 '-threads', '1', str(output)],
                capture_output=True, timeout=12, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            raise VisionError('La capture visuelle a échoué ou dépassé le délai prévu.') from None
        if result.returncode != 0 or not output.is_file():
            raise VisionError('Je ne peux pas lire cette image. Si tu utilises la webcam, vérifie son accès et les autres applications.')
        size = output.stat().st_size
        if not 0 < size <= MAX_IMAGE_BYTES:
            raise VisionError('L’image obtenue est vide ou trop volumineuse pour être analysée.')
        yield output
