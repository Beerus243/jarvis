"""Capture explicite et questions de suivi sur une image temporaire."""
import os

from core.vision.capture import capture_image, VisionError
from core.vision.client import GroqVisionClient
from core.vision.context import visual_session

NO_CONTEXT = 'Je n’ai plus d’image en contexte. Dis « regarde mon écran » ou « regarde avec ma webcam ».'


def _vision_enabled():
    from config import settings
    return os.getenv('JARVIS_VISION_PROVIDER', settings.VISION_PROVIDER).lower() == 'groq'


def analyze_request(request):
    generation = visual_session.clear()
    if not _vision_enabled():
        return 'La vision n’est pas configurée. Choisis son fournisseur avant de demander une analyse.'
    try:
        # Vérifier la configuration avant de solliciter écran ou caméra.
        client = GroqVisionClient()
        source_name = 'écran' if request.source == 'screen' else 'webcam'
        print(f'[VISION] Capture ponctuelle : {source_name}. Analyse par Groq.', flush=True)
        with capture_image(request.source, camera_device=os.getenv('JARVIS_CAMERA_DEVICE', '/dev/video0')) as path:
            answer = client.analyze(path, request.question, request.source)
            if not visual_session.save(generation, path.read_bytes(), request.source, request.question, answer):
                return 'L’analyse a été écartée : le contexte visuel a changé.'
            return answer
    except VisionError as error:
        return str(error)
    except OSError:
        return 'La capture visuelle est inaccessible. Vérifie les périphériques et les fichiers temporaires.'


def followup(question, *, refresh=False):
    if not _vision_enabled():
        visual_session.clear()
        return 'La vision est désactivée. Le contexte visuel a été effacé.'
    context = visual_session.get()
    if context is None:
        return NO_CONTEXT
    if refresh:
        from core.vision.commands import VisionRequest
        return analyze_request(VisionRequest(context.source, question))
    try:
        print('[VISION] Analyse de la dernière image, sans nouvelle capture.', flush=True)
        answer = GroqVisionClient().analyze_image(
            context.image, question, context.source,
            previous=(context.question, context.answer),
        )
        if not visual_session.update(context.generation, question, answer):
            return 'Le contexte visuel a expiré ou a été effacé pendant l’analyse. Demande une nouvelle capture.'
        return answer
    except VisionError as error:
        return str(error)
