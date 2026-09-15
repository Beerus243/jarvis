"""Sessions locales, propositions bornées et reprise explicite (V7)."""
from datetime import datetime
from pathlib import Path
import threading
import time
import uuid

from core.state_store import get_store
from core.proactivity import model, projects


class PersonalAgent:
    def __init__(self, enqueue, *, clock=time.time, monotonic=time.monotonic):
        self.enqueue = enqueue
        self.clock, self.monotonic = clock, monotonic
        self.lock = threading.RLock()
        self.epoch = uuid.uuid4().hex
        self.started = False
        self.presence = {'state': 'unknown'}
        self.sample_at = None
        self.previous = None
        self.session = None
        self.offer = None
        self.last_interaction = 0

    def start(self):
        with self.lock:
            self.started = True
            old = get_store().get('v7', 'offer')
            if old and old['state'] in {'QUEUED', 'DELIVERED', 'DEFERRED', 'EXECUTING'}:
                self.offer = old
                self._finish('INTERRUPTED')
            old_session = get_store().get('v7', 'session')
            if old_session:
                self._archive(old_session, 'interrupted')
            self.session = None
            get_store().delete('v7', 'session')
            model.event('runtime_started', {'epoch': self.epoch}, now=self.clock())

    def stop(self):
        with self.lock:
            self.started = False
            self._finish('CANCELLED')
            if self.session:
                self._archive(self.session, 'stopped')
            self.session = None
            get_store().delete('v7', 'session')

    def _archive(self, session, reason):
        record = {**session, 'ended_at': self.clock(), 'reason': reason}
        get_store().mutate('v7', 'sessions', lambda values:
            ([s for s in (values or []) if s['id'] != session['id']] + [record])[-100:])

    def _save_offer(self):
        get_store().put('v7', 'offer', self.offer)

    def _finish(self, state):
        if not self.offer or self.offer['state'] not in {'QUEUED', 'DELIVERED', 'DEFERRED', 'EXECUTING'}:
            return
        self.offer['state'] = state
        self._save_offer()
        # No call back into Runtime's delivery lock while holding this lock.
        key = self.offer.get('notice_id')
        if key:
            get_store().mutate('notifications', key, lambda n:
                {**n, 'status': 'CANCELLED'} if n and n['status'] == 'PENDING' else n)
        model.event('offer_' + state.lower(), {'id': self.offer['id'], 'kind': self.offer['kind']}, now=self.clock())

    def mode(self):
        return get_store().get('v7', 'availability', 'auto')

    def available(self, *, reminder=False):
        mode = self.mode()
        if mode == 'sleeping':
            return reminder and model.preference('sleep_reminders', False)
        if mode == 'break' or (mode == 'focus' and not reminder):
            return False
        if self.sample_at is None or not 0 <= self.monotonic() - self.sample_at <= 45:
            return False
        return self.presence.get('state') == 'active'

    def touch(self):
        with self.lock:
            self.last_interaction = self.clock()
            if self.presence.get('locked') is False and self.sample_at is not None and 0 <= self.monotonic()-self.sample_at <= 45:
                self.presence = {**self.presence, 'state': 'active', 'source': 'interaction explicite, bureau déverrouillé'}

    def set_mode(self, mode):
        if mode not in {'auto', 'sleeping', 'focus', 'break'}:
            raise ValueError('Disponibilité inconnue.')
        with self.lock:
            if mode == 'break' and self.session:
                model.observe_break(self.session['id'] + ':' + str(self.session['breaks']),
                                    self.session['since_break'], now=self.clock())
                self.session['since_break'] = 0
                self.session['breaks'] += 1
                get_store().put('v7', 'session', self.session)
            get_store().put('v7', 'availability', mode)
            self.previous = None
            self._finish('CANCELLED')
            model.event('availability', {'mode': mode}, now=self.clock())

    def observe(self, pc, presence):
        with self.lock:
            if not self.started:
                return
            now, mono = self.clock(), self.monotonic()
            old_state = self.presence.get('state')
            presence = dict(presence)
            if presence.get('locked') is False and 0 <= now-self.last_interaction < 120:
                presence['state'] = 'active'
                presence['source'] = 'interaction explicite, bureau déverrouillé'
            self.presence = presence
            self.sample_at = mono
            if old_state != presence.get('state'):
                model.event('presence', {'state': presence.get('state')}, now=now)
            context_fresh = 'observed_at' not in pc or 0 <= now-pc['observed_at'] <= 45
            project = projects.identify(pc, get_store().get('v7', 'declared_project')) if context_fresh else None
            key = project['key'] if project else None
            active = presence.get('state') == 'active' and self.mode() in {'auto', 'focus'}
            # Unknown/ambiguous context pauses the session, and invalidates offers.
            if self.offer and (not project or self.offer.get('project') != key):
                self._finish('CANCELLED')
            if active and project:
                if self.session and self.session['project']['key'] != key:
                    self._archive(self.session, 'project_changed')
                    self.session = None
                if self.session is None:
                    self.session = {'id': uuid.uuid4().hex, 'project': project,
                                    'started_at': now, 'active_seconds': 0.0,
                                    'since_break': 0.0, 'breaks': 0}
                    model.event('session_started', {'project': key, 'source': project['source']}, now=now)
                if self.previous:
                    prev_wall, prev_mono, prev_key, prev_active = self.previous
                    delta = mono - prev_mono
                    # Suspension, clock jumps and unknown intervals earn no credit.
                    if prev_active and prev_key == key and 0 <= delta <= 45 and abs((now-prev_wall)-delta) <= 5:
                        self.session['active_seconds'] += delta
                        self.session['since_break'] += delta
                self.session['updated_at'] = now
                get_store().put('v7', 'session', self.session)
            self.previous = (now, mono, key, active)
            self._expire()
            if self.offer and self.offer['state'] == 'DEFERRED' and now >= self.offer['not_before'] and self.available():
                self.offer['state'] = 'QUEUED'
                self.offer['expires_at'] = now + 300
                self.offer['notice_id'] = 'v7:' + self.offer['id'] + ':' + str(int(now))
                self._save_offer()
                self._enqueue_offer()
            if active and project and self.available() and not self.pending():
                self._anticipate(now)

    def _expire(self):
        if self.offer and self.offer['state'] in {'QUEUED', 'DELIVERED'} and self.clock() > self.offer['expires_at']:
            self._finish('EXPIRED')

    def pending(self):
        self._expire()
        return bool(self.offer and self.offer['state'] in {'QUEUED', 'DELIVERED', 'DEFERRED'})

    def _anticipate(self, now):
        if not self.session or get_store().get('settings', 'silent', False):
            return
        if get_store().get('v7', 'suppressed_day') == datetime.fromtimestamp(now).date().isoformat():
            return
        minutes = model.preference('break_minutes')
        if minutes is not None and model.preference('break_proposals', True):
            if self.session['since_break'] >= minutes * 60:
                self.propose('break', automatic=True)
        elif minutes is None and self.session['active_seconds'] >= 600 and model.preference('questions', True):
            self.propose('preference', automatic=True)

    def propose(self, kind='break', *, automatic=False):
        with self.lock:
            if not self.session or (self.previous and self.previous[2] != self.session['project']['key']):
                return 'Indique ton projet avec « je travaille sur NOM », puis utilise sa fenêtre de développement.'
            if self.pending():
                return self.offer['message']
            now = self.clock()
            day = datetime.fromtimestamp(now).date().isoformat()
            budget = get_store().get('v7', 'budget', {})
            if budget.get('day') != day:
                budget = {'day': day, 'questions': 0, 'proposals': 0, 'last_at': 0}
            category = 'questions' if kind == 'preference' else 'proposals'
            episode = f"{kind}:{self.session['id']}:{self.session['breaks']}"
            seen = get_store().get('v7', 'episodes', [])
            limit = model.preference('question_limit', 3) if category == 'questions' else 4
            if automatic and (episode in seen or budget[category] >= limit or now-budget['last_at'] < 1800):
                return None
            if kind == 'preference':
                hypothesis = model.hypothesis(now)
                value = hypothesis['value'] if hypothesis else None
                message = (f"Tes pauses déclarées suggèrent environ {value} minutes de travail. Dis « confirme ma proposition » pour retenir ce rythme."
                           if value else 'Après combien de minutes actives souhaites-tu une pause ? Dis « ma pause après 60 minutes », par exemple.')
            else:
                value = None
                minutes = int(self.session['since_break'] / 60)
                message = (f"Tu as travaillé environ {minutes} minutes actives sur {self.session['project']['name']}. "
                           'Je peux créer un point de reprise local (projet et tâches), puis passer en pause. '
                           + ('Je mettrai aussi la musique en pause. ' if model.preference('pause_music', False) else '') +
                           'Les fichiers ouverts ne seront pas sauvegardés. Dis « confirme ma proposition » ou « refuse ma proposition ».')
            identity = uuid.uuid4().hex
            self.offer = {'id': identity, 'epoch': self.epoch, 'kind': kind, 'state': 'QUEUED' if automatic else 'DELIVERED',
                          'project': self.session['project']['key'], 'path': self.session['project']['path'],
                          'session_id': self.session['id'], 'value': value, 'message': message,
                          'pause_music': bool(model.preference('pause_music', False)),
                          'created_at': now, 'expires_at': now + 300, 'notice_id': 'v7:' + identity,
                          'reason': 'temps actif et préférence confirmée' if kind == 'break' else 'préférence de pause inconnue'}
            self._save_offer()
            get_store().put('v7', 'episodes', (seen + [episode])[-200:])
            if automatic:
                budget[category] += 1
                budget['last_at'] = now
                get_store().put('v7', 'budget', budget)
                self._enqueue_offer()
            model.event('offer_prepared', {'id': identity, 'kind': kind}, now=now)
            return message

    def _enqueue_offer(self):
        self.enqueue(self.offer['notice_id'], self.offer['message'], v7_id=self.offer['id'], now=self.clock(), priority=20)

    def can_deliver(self, notice):
        with self.lock:
            self._expire()
            return bool(self.available() and self.offer and self.offer['state'] == 'QUEUED'
                        and self.offer['id'] == notice.get('v7_id') and self.offer['epoch'] == self.epoch)

    def delivered(self, notice):
        with self.lock:
            if self.offer and self.offer['id'] == notice.get('v7_id') and self.offer['state'] == 'QUEUED':
                self.offer['state'] = 'DELIVERED'
                self.offer['expires_at'] = self.clock() + 300
                self._save_offer()

    def feedback(self, response, minutes=15):
        with self.lock:
            if not self.pending():
                return 'Aucune proposition personnelle en attente.'
            if response == 'refuse':
                self._finish('DECLINED')
                return 'Compris, proposition refusée.'
            if response == 'defer':
                if not 1 <= minutes <= 240:
                    return 'Choisis un report de 1 à 240 minutes.'
                self._finish('DEFERRED')
                self.offer['not_before'] = self.clock() + minutes * 60
                self._save_offer()
                return f'Je reporterai cette proposition de {minutes} minutes, si le même projet est toujours actif.'
            if self.offer['state'] != 'DELIVERED':
                return 'Écoute la proposition avant de la confirmer, ou demande « prépare ma pause ».'
            if self.offer['kind'] == 'preference':
                if self.offer['value'] is None:
                    return 'Dis par exemple « ma pause après 60 minutes ».'
                model.confirm('break_minutes', self.offer['value'], now=self.clock(), source='hypothèse confirmée par Fabrice')
                self._finish('DONE')
                return model.describe()
            if not self.available() or not self.session or self.session['id'] != self.offer['session_id']:
                self._finish('CANCELLED')
                return 'Le contexte a changé ou le PC est indisponible. Prépare une nouvelle pause.'
            project = projects.find_project(self.offer['project'])
            if not project or project['path'] != self.offer['path'] or not Path(project['path']).is_dir():
                self._finish('CANCELLED')
                return 'Le chemin du projet a changé ou est indisponible. Aucun point de reprise créé.'
            self.offer['state'] = 'EXECUTING'
            self._save_offer()  # Persist consumption before effects; never replay at restart.
            from core.task_engine import list_tasks
            point = {'id': self.offer['id'], 'project': project, 'at': self.clock(),
                     'active_seconds': self.session['active_seconds'],
                     'tasks': [{'id': t.id, 'goal': t.goal, 'status': t.status} for t in list_tasks() if t.status not in {'COMPLETED', 'CANCELLED'}],
                     'editor_files_saved': False}
            try:
                get_store().put('v7_checkpoints', point['id'], point)
                if get_store().get('v7_checkpoints', point['id']) != point:
                    raise OSError('Vérification du point de reprise échouée.')
                points = sorted(get_store().items('v7_checkpoints'), key=lambda pair: pair[1]['at'])
                for key, _ in points[:-30]:
                    get_store().delete('v7_checkpoints', key)
            except Exception:
                self._finish('FAILED')
                return 'Le point de reprise n’a pas pu être vérifié. Je ne passe pas en pause.'
            action_message = ''
            if self.offer.get('pause_music'):
                from core.action_executor import execute_action
                identity = self.offer['id']
                # Native PC action may be slow; cancellation and stop stay responsive.
                self.lock.release()
                try:
                    result = execute_action({'action': 'MEDIA_PAUSE'}, confirmation=True)
                finally:
                    self.lock.acquire()
                if not self.offer or self.offer['id'] != identity or self.offer['state'] != 'EXECUTING':
                    return 'Routine interrompue. Le point de reprise existe ; vérifie le lecteur si sa pause était déjà en cours.'
                if not result.success:
                    self._finish('FAILED')
                    return 'Point de reprise vérifié, mais la pause de la musique a échoué. Je reste disponible. ' + result.message
                action_message = ' Musique mise en pause selon le retour du lecteur.'
            self._finish('DONE')
            self.set_mode('break')
            return f"Point de reprise vérifié pour {project['name']}. Je passe en pause. Pense à sauvegarder les fichiers de ton éditeur." + action_message

    def status(self):
        with self.lock:
            session = self.session
            detail = (f"Projet : {session['project']['name']}, environ {int(session['active_seconds']/60)} minutes actives observées. "
                      if session else 'Aucune session de projet reconnue. ')
            return f"Disponibilité : {self.mode()}, présence : {self.presence.get('state', 'unknown')}. " + detail + model.describe()
