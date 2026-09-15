"""Capture explicite et questions de suivi sur une image temporaire."""
import os

from core.vision.capture import capture_image, VisionError
from core.vision.client import GroqVisionClient
from core.vision.context import visual_session

NO_CONTEXT = 'Je n’ai plus d’image en contexte. Dis « regarde mon écran » ou « regarde avec ma webcam ».'


def _vision_enabled():
    from core.vision.providers import provider_name
    return provider_name() in {'groq', 'local'}


def analyze_request(request):
    generation = visual_session.clear()
    if not _vision_enabled():
        return 'La vision n’est pas configurée. Choisis son fournisseur avant de demander une analyse.'
    try:
        # Vérifier la configuration avant de solliciter écran ou caméra.
        from core.vision.providers import get_client, provider_name
        provider = provider_name()
        client = get_client(groq_factory=GroqVisionClient, name=provider)
        source_name = request.target.label if request.target else ('écran' if request.source == 'screen' else 'webcam')
        print(f'[VISION] Capture ponctuelle : {source_name}. Analyse par {provider}.', flush=True)
        options = {'target': request.target} if request.target else {}
        with capture_image(request.source, camera_device=os.getenv('JARVIS_CAMERA_DEVICE', '/dev/video0'), **options) as path:
            if not visual_session.is_current(generation):
                return 'Capture écartée : le contexte visuel a changé.'
            evidence = None
            if request.mode == 'read':
                from core.vision.evidence import read_image, format_reading
                evidence = read_image(client, path.read_bytes(), request.source)
                answer = format_reading(evidence)
            else:
                answer = client.analyze(path, request.question, request.source)
            if not visual_session.save(generation, path.read_bytes(), request.source, request.question, answer, target=request.target, provider=provider, evidence=evidence):
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
    from core.vision.providers import provider_name, get_client
    if context.provider and context.provider != provider_name():
        visual_session.clear()
        return 'Fournisseur modifié : demande une nouvelle capture.'
    if refresh:
        from core.vision.commands import VisionRequest
        return analyze_request(VisionRequest(context.source, question, target=context.target))
    try:
        print('[VISION] Analyse de la dernière image, sans nouvelle capture.', flush=True)
        answer = get_client(groq_factory=GroqVisionClient, name=context.provider or provider_name()).analyze_image(
            context.image, question, context.source,
            previous=(context.question, context.answer),
        )
        if not visual_session.update(context.generation, question, answer):
            return 'Le contexte visuel a expiré ou a été effacé pendant l’analyse. Demande une nouvelle capture.'
        return answer
    except VisionError as error:
        return str(error)
