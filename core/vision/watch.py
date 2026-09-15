"""Surveillance d'écran bornée ; aucune capture sans démarrage explicite."""
import hashlib
import threading
import time
import uuid

from core.vision.capture import capture_image, VisionError
from core.vision.client import GroqVisionClient

GOALS = {'compilation': 'de la compilation', 'download': 'du téléchargement', 'error': 'des erreurs à l’écran'}


def capture_screen():
    with capture_image('screen') as path:
        return path.read_bytes()


def assess_screen(data, goal):
    from core.vision.providers import get_client
    return get_client(groq_factory=GroqVisionClient).assess_image(data, goal)


class VisualWatch:
    def __init__(self, enqueue, cancel_notifications, *, busy=None, capture=None,
                 assess=None, enabled=None, clock=time.monotonic):
        self.enqueue = enqueue
        self.cancel_notifications = cancel_notifications
        self.busy = busy or threading.Event()
        self.capture = capture or capture_screen
        self.assess = assess or assess_screen
        self.enabled = enabled or (lambda: True)
        self.clock = clock
        self._lock = threading.RLock()
        self._operation = threading.Lock()
        self._job = None

    def start(self, goal, *, duration=300, interval=30, max_analyses=10, target=None, provider=None, owner=None):
        if (goal not in GOALS or any(type(n) is not int for n in (duration, interval, max_analyses))
                or not 60 <= duration <= 900 or not 30 <= interval <= duration or not 1 <= max_analyses <= 10):
            raise ValueError('Surveillance : durée de 1 à 15 minutes, intervalle minimal de 30 secondes, 10 analyses maximum.')
        from core.vision.providers import provider_name
        from core.vision.targets import pin_window
        if target and target.kind == 'region' and target.rect is None:
            raise VisionError('La surveillance nécessite une zone fixe en pixels.')
        if target and target.kind == 'window' and target.window_id is None:
            target = pin_window(target)
        self.expire()
        with self._lock:
            if self._job and self._job['state'] == 'RUNNING':
                return 'Une surveillance est déjà active. Arrête-la avant d’en démarrer une autre.'
            previous_id = self._job['id'] if self._job else None
            now = self.clock()
            self._job = dict(id=uuid.uuid4().hex[:8], goal=goal, state='RUNNING',
                             deadline=now + duration, next_at=now, interval=interval,
                             max_analyses=max_analyses, analyses=0, captures=0,
                             errors=0, signature=None, candidate=None, matches=0,
                             target=target, provider=provider or provider_name(), fingerprint=None, skipped=0, owner=owner)
        if previous_id:
            self.cancel_notifications(previous_id)
        unit = 'minute' if duration == 60 else 'minutes'
        return (f"Surveillance {GOALS[goal]} activée sur {target.label if target else 'l’écran'} pendant {duration // 60} {unit}. "
                f'Au plus {max_analyses} analyses {provider or provider_name()}, espacées d’au moins {interval} secondes. '
                'Garde la fenêtre concernée visible. Dis « arrête la surveillance » pour arrêter.')

    def stop(self):
        with self._lock:
            if not self._job:
                return 'Aucune surveillance visuelle active.'
            job_id = self._job['id']
            self._job['state'] = 'CANCELLED'
            self._job['signature'] = self._job['candidate'] = self._job['fingerprint'] = None
        self.cancel_notifications(job_id)
        return 'Surveillance visuelle arrêtée.'

    def snapshot(self):
        self.expire()
        with self._lock:
            return {k: v for k, v in self._job.items() if k != 'fingerprint'} if self._job else None

    def status(self):
        job = self.snapshot()
        if not job:
            return 'Aucune surveillance visuelle active.'
        labels = {'RUNNING': 'active', 'CANCELLED': 'arrêtée', 'COMPLETED': 'événement détecté',
                  'EXPIRED': 'durée écoulée', 'LIMIT': 'limite atteinte', 'FAILED': 'indisponible'}
        remaining = max(0, int(job['deadline'] - self.clock())) if job['state'] == 'RUNNING' else 0
        return (f"Surveillance {GOALS[job['goal']]} : {labels[job['state']]}. "
                f"{job['analyses']}/{job['max_analyses']} analyses, {remaining} secondes restantes.")

    def _active(self, job_id):
        return self._job and self._job['id'] == job_id and self._job['state'] == 'RUNNING'

    def _finish(self, state, message):
        # Appelé sous verrou : arrêter ne peut pas être suivi d'une alerte tardive.
        job = self._job
        job['state'] = state
        job['signature'] = job['candidate'] = job['fingerprint'] = None
        self.enqueue('vision-watch:' + job['id'], message, visual_watch_id=job['id'])

    def expire(self):
        with self._lock:
            if self._job and self._job['state'] == 'RUNNING' and self.clock() >= self._job['deadline']:
                self._finish('EXPIRED', 'Surveillance visuelle terminée : durée écoulée, sans événement confirmé.')

    def step(self):
        self.expire()
        if not self._operation.acquire(blocking=False):
            return
        try:
            with self._lock:
                job = self._job
                if not job or job['state'] != 'RUNNING':
                    return
                from core.vision.providers import provider_name
                if not self.enabled() or provider_name() != job['provider']:
                    self._finish('FAILED', 'Surveillance arrêtée : la vision est désactivée.')
                    return
                if self.busy.is_set() or self.clock() < job['next_at']:
                    return
                job_id, goal = job['id'], job['goal']
                job['captures'] += 1
            try:
                if job['target'] is not None:
                    with capture_image('screen', target=job['target']) as path:
                        data = path.read_bytes()
                else:
                    data = self.capture()
                from core.vision.changes import fingerprint, meaningful_change
                pixels = fingerprint(data)
                signature = hashlib.sha256(data).hexdigest()
                self.expire()
                with self._lock:
                    if not self._active(job_id) or not self.enabled() or provider_name() != self._job['provider']:
                        return
                    job = self._job
                    if (signature == job['signature'] or not meaningful_change(job['fingerprint'], pixels)) and not job['candidate']:
                        job['errors'] = 0
                        job['skipped'] += 1
                        return
                    if job['analyses'] >= job['max_analyses']:
                        self._finish('LIMIT', 'Surveillance terminée : limite d’analyses atteinte, sans événement confirmé.')
                        return
                    job['analyses'] += 1
                if self.assess is assess_screen:
                    from core.vision.providers import get_client
                    result = get_client(groq_factory=GroqVisionClient, name=job['provider']).assess_image(data, goal)
                else:
                    result = self.assess(data, goal)
                # Les octets de surveillance ne rejoignent jamais VisualSession.
                del data
                self.expire()
                with self._lock:
                    if not self._active(job_id) or not self.enabled() or provider_name() != self._job['provider']:
                        return
                    job = self._job
                    state, evidence = result['state'], result['evidence']
                    if state not in {'waiting', 'complete', 'error', 'unknown'} or not isinstance(evidence, str):
                        raise VisionError('Observation visuelle invalide.')
                    job['errors'] = 0
                    job['signature'] = signature
                    job['fingerprint'] = pixels
                    terminal = bool(evidence.strip()) and (state == 'error' or (state == 'complete' and goal != 'error'))
                    job['matches'] = job['matches'] + 1 if terminal and state == job['candidate'] else int(terminal)
                    job['candidate'] = state if terminal else None
                    if job['matches'] >= 2:
                        label = ('Une erreur apparaît à l’écran' if state == 'error' else
                                 'La compilation semble terminée à l’écran' if goal == 'compilation' else
                                 'Le téléchargement semble terminé à l’écran')
                        self._finish('COMPLETED', f'{label}. {evidence[:500]}')
                    elif job['analyses'] >= job['max_analyses']:
                        self._finish('LIMIT', 'Surveillance terminée : limite d’analyses atteinte, sans événement confirmé.')
            except Exception:
                with self._lock:
                    if self._active(job_id):
                        job = self._job
                        job['errors'] += 1
                        job['candidate'] = None
                        job['matches'] = 0
                        if job['errors'] >= 3:
                            self._finish('FAILED', 'Surveillance arrêtée après trois échecs. Vérifie la capture et l’accès au fournisseur de vision.')
                        elif job['analyses'] >= job['max_analyses']:
                            self._finish('LIMIT', 'Surveillance arrêtée : limite d’analyses atteinte.')
            finally:
                with self._lock:
                    if self._active(job_id):
                        self._job['next_at'] = self.clock() + self._job['interval']
        finally:
            self._operation.release()
