"""Horloge proactive et exécution des tâches, indépendantes de l'entrée utilisateur."""
from datetime import datetime
import queue
import threading
import time
import uuid
import fcntl

from core.state_store import get_store

_runtime = None


def add_reminder(message, due_at):
    if not message.strip() or due_at <= time.time():
        raise ValueError('Le rappel doit avoir un texte et une date future.')
    item = {'id': uuid.uuid4().hex[:8], 'message': message.strip(), 'due_at': due_at, 'status': 'SCHEDULED'}
    get_store().put('reminders', item['id'], item)
    return item


class Runtime:
    def __init__(self, *, notify=None, pc_provider=None, personal_provider=None, interval=1.0, dispatcher=None):
        self.notify = notify
        self.pc_provider = pc_provider
        self.personal_provider = personal_provider
        self.interval = interval
        self.dispatcher = dispatcher
        self.busy = threading.Event()
        self.stopping = threading.Event()
        self.jobs = queue.Queue()
        self._scheduled = set()
        self._lock = threading.Lock()
        self._delivery_lock = threading.Lock()
        self._process_lock = None
        self._last_observation = 0
        self.threads = []
        from core.vision.watch import VisualWatch
        from core.vision.service import _vision_enabled
        self.visual_watch = VisualWatch(self.enqueue, self.cancel_visual_notifications,
                                       busy=self.busy, enabled=_vision_enabled)

    def start(self):
        global _runtime
        if self.threads:
            return self
        path = get_store().path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._process_lock = open(str(path) + '.lock', 'a')
        try:
            fcntl.flock(self._process_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._process_lock.close()
            self._process_lock = None
            raise RuntimeError('Une session Jarvis proactive utilise déjà cette base. Ferme-la ou utilise --no-proactive.')
        _runtime = self
        # Les surveillances ne reprennent pas après un redémarrage, et leurs
        # annonces non lues ne doivent pas sembler concerner la nouvelle session.
        self.cancel_visual_notifications()
        # Les tâches interrompues ne sont jamais relancées sans commande explicite.
        from core.task_engine import list_tasks, pause_task
        for task in list_tasks():
            if task.status == 'RUNNING':
                pause_task(task.id)
        for target in (self._clock, self._worker, self._watch_loop):
            # La surveillance finit son appel borné et nettoie ses captures
            # avant la sortie du processus, même si stop() rend la main avant.
            thread = threading.Thread(target=target, daemon=target != self._watch_loop)
            thread.start()
            self.threads.append(thread)
        return self

    def stop(self):
        global _runtime
        self.stopping.set()
        self.visual_watch.stop()
        from core.task_engine import list_tasks, pause_task
        for task in list_tasks():
            if task.status == 'RUNNING':
                pause_task(task.id)
        for thread in self.threads:
            thread.join(timeout=2)
        if self._process_lock and not any(thread.is_alive() for thread in self.threads):
            self._process_lock.close()
            self._process_lock = None
        if _runtime is self:
            _runtime = None

    def submit(self, task_id, *, confirmation=False):
        with self._lock:
            if task_id in self._scheduled:
                return False
            self._scheduled.add(task_id)
            self.jobs.put((task_id, confirmation))
        return True

    def _worker(self):
        from core.task_engine import execute_task, load_task
        while not self.stopping.is_set():
            try:
                task_id, confirmation = self.jobs.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                task = load_task(task_id)
                if task:
                    task, _ = execute_task(task, confirmation=confirmation, dispatcher=self.dispatcher)
                    self.enqueue(f'task:{task.id}:{task.status}:{task.current_step}',
                        f"Tâche {task.id[:8]} : {task.status}. {task.error or task.goal}")
            except Exception as error:
                self.enqueue(f'task-error:{task_id}', f'Tâche interrompue : {error}')
            finally:
                with self._lock:
                    self._scheduled.discard(task_id)
                self.jobs.task_done()

    def enqueue(self, key, message, *, reminder_id=None, now=None, visual_watch_id=None):
        now = time.time() if now is None else now
        def insert(value):
            return value or {'id': key, 'message': message, 'status': 'PENDING',
                             'created_at': now, 'reminder_id': reminder_id,
                             'visual_watch_id': visual_watch_id}
        return get_store().mutate('notifications', key, insert)

    def cancel_visual_notifications(self, watch_id=None):
        with self._delivery_lock:
            store = get_store()
            for key, notice in store.items('notifications'):
                if (notice.get('visual_watch_id') and notice['status'] == 'PENDING'
                        and (watch_id is None or notice['visual_watch_id'] == watch_id)):
                    store.mutate('notifications', key, lambda n: {**n, 'status': 'CANCELLED'} if n else None)

    def tick(self, now=None):
        self.visual_watch.expire()
        now = time.time() if now is None else now
        store = get_store()
        # Notification durable : un redémarrage ne perd pas un rappel échu.
        for key, reminder in store.items('reminders'):
            if reminder['status'] == 'SCHEDULED' and reminder['due_at'] <= now:
                self.enqueue(f"reminder:{key}:{reminder['due_at']}", f"Rappel : {reminder['message']}", reminder_id=key, now=now)
        if now - self._last_observation >= 30:
            self._last_observation = now
            self._observe(now)
        if self.notify is not None:
            self.deliver(self.notify, now=now)

    def _observe(self, now):
        from core.pc_context import get_pc_context
        from memory.personal_state import get_personal_context
        from memory.pc_proactive import detect_pc_proposals
        from memory.proactive import detect_proposals
        pc = (self.pc_provider or get_pc_context)()
        personal = (self.personal_provider or get_personal_context)()
        store = get_store()
        battery = pc.get('battery') or {}
        if battery.get('charging') or (battery.get('level') is not None and battery['level'] >= 25):
            store.delete('attention', 'low_battery')
        current = datetime.fromtimestamp(now).astimezone()
        proposals = detect_pc_proposals(personal, pc, now=current)
        proposals += detect_proposals(personal, now=current)
        for proposal in proposals:
            kind = proposal['type']
            episode = kind if kind == 'low_battery' else f"{kind}:{personal.get('started_at')}"
            if store.get('attention', episode):
                continue
            self.enqueue('proposal:' + episode + ':' + str(int(now)), proposal['reason'], now=now)
            store.put('attention', episode, {'created_at': now})

    def deliver(self, sink, now=None):
        with self._delivery_lock:
            return self._deliver(sink, now)

    def _deliver(self, sink, now=None):
        now = time.time() if now is None else now
        store = get_store()
        if self.busy.is_set() or store.get('settings', 'silent', False):
            return []
        delivered = []
        # Une seule annonce à la fois, ordre chronologique.
        pending = sorted((v for _, v in store.items('notifications') if v['status'] == 'PENDING'), key=lambda v: v['created_at'])
        for notice in pending[:1]:
            if not notice.get('reminder_id') and now - notice['created_at'] > 3600:
                notice['status'] = 'EXPIRED'
                store.put('notifications', notice['id'], notice)
                continue
            if sink(notice['message']) is False:
                continue
            notice['status'] = 'DELIVERED'
            store.put('notifications', notice['id'], notice)
            store.put('session', 'last_notification', notice)
            if notice.get('reminder_id'):
                store.mutate('reminders', notice['reminder_id'], lambda item: {**item, 'status': 'DELIVERED'} if item else None)
            delivered.append(notice)
        return delivered

    def _clock(self):
        while not self.stopping.wait(self.interval):
            try:
                self.tick()
            except Exception as error:
                # Un capteur absent ne doit pas tuer l'horloge des rappels.
                get_store().put('health', 'runtime', {'error': str(error), 'at': time.time()})

    def _watch_loop(self):
        while not self.stopping.wait(0.25):
            try:
                self.visual_watch.step()
            except Exception:
                self.visual_watch.stop()
                get_store().put('health', 'vision_watch', {'error': 'Surveillance interrompue.', 'at': time.time()})


def get_runtime():
    return _runtime
