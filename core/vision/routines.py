"""Règle contextuelle opt-in, bornée à cette session, sans reprise automatique."""
from datetime import datetime
import threading
import time
import uuid

from core.state_store import get_store
from core.vision.capture import VisionError
from core.vision.targets import selected_target, pin_window
from core.vision.providers import provider_name, get_client


class VisualRoutines:
    def __init__(self, watch, *, pc_provider=None, clock=time.monotonic):
        self.watch, self.pc_provider, self.clock = watch, pc_provider, clock
        self._lock = threading.RLock()
        self._rule = None

    def start(self, *, duration=900, hours=None):
        if type(duration) is not int or not 60 <= duration <= 900:
            raise VisionError('Routine limitée de 1 à 15 minutes.')
        if hours is not None and (len(hours) != 2 or any(type(h) is not int or not 0 <= h <= 23 for h in hours)):
            raise VisionError('Horaire invalide : heures de 0 à 23.')
        get_client()  # Précontrôle sans image.
        target = selected_target()
        if target.kind == 'region' and target.rect is None:
            raise VisionError('Définis une zone fixe avant d’activer la routine.')
        if target.kind == 'window':
            target = pin_window(target)
        with self._lock:
            if self._rule and self._rule['state'] in {'ARMED', 'WATCHING'}:
                return 'La routine de développement est déjà activée.'
            self._rule = dict(state='ARMED', deadline=self.clock() + duration, hours=hours,
                              target=target, provider=provider_name(), watch_id=None, next_check=0, id=uuid.uuid4().hex)
            get_store().put('visual_routines', 'development', {'schema': 1, 'state': 'SESSION_ONLY', 'hours': hours})
        return f'Routine de développement activée pour {duration // 60} minutes sur {target.label}. Une seule surveillance, dix analyses maximum ; arrêt au redémarrage.'

    def stop(self):
        with self._lock:
            rule = self._rule
            if rule:
                rule['state'] = 'DISABLED'
                job = self.watch.snapshot()
                if job and job['id'] == rule['watch_id']:
                    self.watch.stop()
            get_store().put('visual_routines', 'development', {'schema': 1, 'state': 'DISABLED'})
        return 'Routine visuelle désactivée.'

    def status(self):
        with self._lock:
            rule = self._rule
            if not rule:
                return 'Aucune routine visuelle active. Les routines ne reprennent pas au redémarrage.'
            states = {'ARMED': 'en attente de contexte', 'WATCHING': 'surveillance active', 'DONE': 'terminée', 'DISABLED': 'désactivée', 'EXPIRED': 'expirée'}
            return f"Routine développement : {states[rule['state']]}, {max(0, int(rule['deadline'] - self.clock()))} secondes restantes."

    def step(self, now=None):
        with self._lock:
            rule = self._rule
            if not rule or rule['state'] not in {'ARMED', 'WATCHING'}:
                return
            if self.clock() >= rule['deadline'] or provider_name() != rule['provider']:
                self.stop()
                rule['state'] = 'EXPIRED'
                return
            job = self.watch.snapshot()
            if rule['state'] == 'WATCHING':
                if not job or job['id'] != rule['watch_id'] or job['state'] != 'RUNNING':
                    rule['state'] = 'DONE'
                return
            if job and job['state'] == 'RUNNING':
                return
            if get_store().get('settings', 'silent', False) or self.watch.busy.is_set():
                return
            hour = datetime.fromtimestamp(time.time() if now is None else now).hour
            if rule['hours']:
                start, end = rule['hours']
                in_hours = start <= hour < end if start < end else hour >= start or hour < end
                if not in_hours:
                    return
            if self.clock() < rule['next_check']:
                return
            rule['next_check'] = self.clock() + 30
            from core.pc_context import get_pc_context
            from core.task_engine import list_tasks
            pc = (self.pc_provider or get_pc_context)()
            active = pc.get('active_window', {})
            coding = active.get('available') and any(name in str(active.get('application', '')).lower() for name in ('code', 'konsole', 'terminal', 'pycharm', 'kate'))
            coding = coding or any(t.status == 'RUNNING' and any(w in t.goal.lower() for w in ('compil', 'test', 'code')) for t in list_tasks())
            if not coding:
                return
            remaining = min(900, int(rule['deadline'] - self.clock()))
            if remaining < 60:
                rule['state'] = 'EXPIRED'
                return
            self.watch.start('error', duration=remaining, target=rule['target'], provider=rule['provider'], owner=rule['id'])
            job = self.watch.snapshot()
            if job and job['state'] == 'RUNNING' and job.get('owner') == rule['id']:
                rule['watch_id'], rule['state'] = job['id'], 'WATCHING'
