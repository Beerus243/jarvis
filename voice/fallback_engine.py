"""Synthèse locale française de secours via eSpeak, sans téléchargement de modèle."""
import os
import shutil
import subprocess
import tempfile


class EspeakEngine:
    def generate(self, text):
        executable = shutil.which('espeak-ng') or shutil.which('espeak')
        if not executable:
            raise RuntimeError('Kokoro et eSpeak sont indisponibles.')
        fd, path = tempfile.mkstemp(prefix='jarvis-', suffix='.wav')
        os.close(fd)
        try:
            subprocess.run([executable, '-v', 'fr-fr', '-s', '165', '-w', path, '--stdin'],
                           input=str(text), text=True, check=True, capture_output=True, timeout=30)
            return path
        except BaseException:
            os.unlink(path)
            raise
