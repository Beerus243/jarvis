"""Comparaison locale en niveaux de gris ; aucun contenu persistant."""
import subprocess

WIDTH, HEIGHT = 320, 180
PIXEL_DELTA = 24
CHANGED_FRACTION = 0.003  # 0,3 % ; compromis vérifié par fixtures, pas une garantie OCR.


def fingerprint(data):
    if len(data) < 64:
        return None
    try:
        result = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', 'pipe:0',
            '-frames:v', '1', '-vf', f'scale={WIDTH}:{HEIGHT}', '-threads', '1',
            '-f', 'rawvideo', '-pix_fmt', 'gray', 'pipe:1'], input=data, capture_output=True, timeout=5)
        if result.returncode == 0 and len(result.stdout) == WIDTH * HEIGHT:
            return result.stdout
    except (OSError, subprocess.SubprocessError):
        pass
    return None  # En cas d'échec, conserver la comparaison exacte et analyser.


def meaningful_change(before, after):
    if before is None or after is None or len(before) != len(after):
        return True
    return sum(abs(a - b) >= PIXEL_DELTA for a, b in zip(before, after)) / len(after) >= CHANGED_FRACTION
