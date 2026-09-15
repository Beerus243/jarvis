"""Choix de session explicite, budget partagé et fournisseur local sans repli cloud."""
import base64
from collections import deque
import json
import os
import threading
import time
from urllib import request

from core.vision.capture import MAX_IMAGE_BYTES, VisionError
from core.vision.client import GroqVisionClient, SYSTEM_PROMPT

_lock = threading.RLock()
_override = None
_attempts = deque()
_metrics = {}


def provider_name():
    from config import settings
    with _lock:
        return _override or os.getenv('JARVIS_VISION_PROVIDER', settings.VISION_PROVIDER).lower()


def reset_session():
    global _override
    with _lock:
        _override = None
        _attempts.clear()
        _metrics.clear()


def metrics():
    with _lock:
        return {k: dict(v) for k, v in _metrics.items()}


def quota():
    try:
        return max(1, min(120, int(os.getenv('JARVIS_VISION_HOURLY_LIMIT', '30'))))
    except ValueError:
        return 30


class MeasuredClient:
    def __init__(self, client, provider):
        self.client, self.provider = client, provider

    def _call(self, method, *args, **kwargs):
        if provider_name() != self.provider:
            raise VisionError('Le fournisseur a changé ; analyse annulée avant envoi.')
        start = time.monotonic()
        with _lock:
            while _attempts and _attempts[0] <= start - 3600:
                _attempts.popleft()
            if len(_attempts) >= quota():
                raise VisionError('Quota visuel de session atteint pour cette heure. Aucune nouvelle image envoyée.')
            _attempts.append(start)
        ok = False
        try:
            result = getattr(self.client, method)(*args, **kwargs)
            ok = True
            return result
        finally:
            elapsed = round(time.monotonic() - start, 3)
            with _lock:
                item = _metrics.setdefault(self.provider, {'calls': 0, 'errors': 0, 'total_seconds': 0, 'last_seconds': 0})
                item['calls'] += 1
                item['errors'] += int(not ok)
                item['total_seconds'] = round(item['total_seconds'] + elapsed, 3)
                item['last_seconds'] = elapsed

    def analyze(self, *args, **kwargs):
        return self._call('analyze', *args, **kwargs)

    def analyze_image(self, *args, **kwargs):
        return self._call('analyze_image', *args, **kwargs)

    def assess_image(self, *args, **kwargs):
        return self._call('assess_image', *args, **kwargs)


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class LocalVisionClient(GroqVisionClient):
    """API Ollama locale uniquement. Le modèle doit déjà être installé."""
    def __init__(self, model=None):
        self.model = model or os.getenv('JARVIS_LOCAL_VISION_MODEL', '')
        if not self.model or 'cloud' in self.model.lower() or '://' in self.model:
            raise VisionError('Vision locale indisponible : configure un modèle visuel installé dans JARVIS_LOCAL_VISION_MODEL. Aucun repli vers Groq.')
        info = self._post('show', {'model': self.model}, timeout=3)
        capabilities = info.get('capabilities')
        if (info.get('remote_host') or info.get('remote_model') or
                not isinstance(capabilities, list) or 'vision' not in capabilities):
            raise VisionError('Ce modèle Ollama n’est pas une vision locale vérifiée. Aucun envoi cloud.')

    def _post(self, endpoint, payload, timeout=60):
        try:
            opener = request.build_opener(request.ProxyHandler({}), _NoRedirect())
            req = request.Request('http://127.0.0.1:11434/api/' + endpoint,
                data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
            with opener.open(req, timeout=timeout) as response:
                raw = response.read(128 * 1024 + 1)
            if len(raw) > 128 * 1024:
                raise ValueError('response size')
            result = json.loads(raw)
            if not isinstance(result, dict) or result.get('error'):
                raise ValueError('response')
            return result
        except (OSError, ValueError):
            raise VisionError('Le modèle local ne répond pas ou n’est pas installé. Aucun repli vers Groq.') from None

    def analyze_image(self, data, question, source, *, previous=None, response_format=None):
        if not data.startswith(b'\xff\xd8\xff') or len(data) > MAX_IMAGE_BYTES:
            raise VisionError('Image JPEG invalide ou trop volumineuse.')
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        if previous:
            messages += [{'role': 'user', 'content': previous[0][:2000]}, {'role': 'assistant', 'content': previous[1][:6000]}]
        messages.append({'role': 'user', 'content': question, 'images': [base64.b64encode(data).decode('ascii')]})
        payload = {'model': self.model, 'messages': messages, 'stream': False,
                   'options': {'temperature': 0, 'num_predict': 600}, 'keep_alive': '2m'}
        if response_format:
            payload['format'] = 'json'
        result = self._post('chat', payload)
        message = result.get('message')
        if not isinstance(message, dict):
            raise VisionError('Le modèle local a retourné une réponse invalide. Aucun repli vers Groq.')
        answer = message.get('content')
        if not isinstance(answer, str) or not answer.strip():
            raise VisionError('Le modèle local n’a retourné aucune description.')
        return answer.strip()


def get_client(*, groq_factory=None, name=None):
    name = name or provider_name()
    if name == 'groq':
        client = (groq_factory or GroqVisionClient)()
    elif name == 'local':
        client = LocalVisionClient()
    else:
        raise VisionError('La vision est désactivée ou son fournisseur est inconnu.')
    return MeasuredClient(client, name)


def switch_provider(name):
    global _override
    if name not in {'groq', 'local', 'disabled'}:
        raise VisionError('Choisis Groq, locale ou désactivée.')
    # Appliquer le choix AVANT le précontrôle : un échec local reste local.
    with _lock:
        _override = name
    from core.vision.context import visual_session
    from core.runtime import get_runtime
    visual_session.clear()
    runtime = get_runtime()
    if runtime:
        runtime.visual_watch.stop()
        runtime.visual_routines.stop()
    if name != 'disabled':
        get_client()
    return ('Vision désactivée pour cette session.' if name == 'disabled' else
            f'Vision {name} sélectionnée pour cette session. Contexte précédent effacé et surveillance arrêtée.')
