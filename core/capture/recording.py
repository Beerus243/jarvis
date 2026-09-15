"""Une vidéo Spectacle appartenant à Jarvis, bornée et finalisée à l'arrêt.

KDE Wayland : sélection native, aucune capture audio ajoutée par Jarvis.
Les appels D-Bus ciblent le nom de connexion unique du processus vérifié.
"""
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import tempfile
import time
from uuid import uuid4

from core.actions.models import ActionResult

BUS = 'org.freedesktop.DBus'
BUS_PATH = '/org/freedesktop/DBus'


class ScreenRecorder:
    def __init__(self, destination=None, *, runner=None, popen=None, clock=time.monotonic):
        self.destination = Path(destination or Path.home() / 'Videos' / 'Jarvis')
        self.run = runner or subprocess.run
        self.popen = popen or subprocess.Popen
        self.clock = clock
        self.lock = threading.RLock()
        self.process = None
        self.owner = None
        self.target = None
        self.deadline = 0
        self.last = None
        self.watcher = None
        self.done = threading.Event()
        self.log_file = None

    def _call(self, dest, path, method, *args):
        result = self.run(['gdbus', 'call', '--session', '--dest', dest,
                           '--object-path', path, '--method', method, *args],
                          capture_output=True, text=True, timeout=5, check=False)
        if result.returncode:
            raise OSError('DBUS_UNAVAILABLE')
        return result.stdout.strip()

    def _owner(self):
        present = self._call(BUS, BUS_PATH, BUS + '.NameHasOwner', 'org.kde.Spectacle')
        if present == '(false,)':
            return None
        value = self._call(BUS, BUS_PATH, BUS + '.GetNameOwner', 'org.kde.Spectacle')
        match = re.fullmatch(r"\('(:[0-9]+\.[0-9]+)',\)", value)
        if not match:
            raise OSError('INVALID_DBUS_OWNER')
        return match[1]

    def _owns(self, owner):
        value = self._call(BUS, BUS_PATH, BUS + '.GetConnectionUnixProcessID', owner)
        return value == f'(uint32 {self.process.pid},)'

    @staticmethod
    def _result(action, success, message, error=None, path=None):
        return ActionResult(action, success, message, artifact_path=str(path) if path else None, error=error)

    def start(self, scope='screen', duration=60):
        with self.lock:
            if self.process is not None:
                return self._result('RECORDING_START', False, 'Une session vidéo est déjà active. Dis « arrête la vidéo ».', 'ALREADY_RECORDING')
            if scope not in {'screen', 'window', 'region'} or type(duration) is not int or not 5 <= duration <= 900:
                return self._result('RECORDING_START', False, 'Choisis l’écran, une fenêtre ou une zone, pendant 5 secondes à 15 minutes.', 'INVALID_RECORDING')
            if os.environ.get('XDG_SESSION_TYPE') != 'wayland' or not all(shutil.which(tool) for tool in ('spectacle', 'gdbus', 'ffprobe')):
                return self._result('RECORDING_START', False, 'La vidéo nécessite KDE Wayland, Spectacle et FFmpeg.', 'RECORDING_UNAVAILABLE')
            try:
                if self._owner():
                    return self._result('RECORDING_START', False, 'Spectacle est déjà ouvert. Ferme sa session avant de démarrer une vidéo avec Jarvis.', 'SPECTACLE_BUSY')
                self.destination.mkdir(parents=True, exist_ok=True)
                self.target = self.destination / f'video_{scope}_{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:8]}.webm'
                self.done = threading.Event()
                self.last = None
                self.log_file = tempfile.TemporaryFile()
                self.process = self.popen(['spectacle', '--background', '--nonotify', '--record', scope,
                                           '--output', str(self.target)],
                                          stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=self.log_file)
                limit = self.clock() + 20
                while self.process.poll() is None and self.clock() < limit:
                    owner = self._owner()
                    if owner and self._owns(owner):
                        self.owner = owner
                        break
                    time.sleep(.1)
                else:
                    raise OSError('RECORDING_START_FAILED')
                # Limite totale incluant la sélection : aucune sélection laissée ouverte indéfiniment.
                self.deadline = self.clock() + duration
                self.watcher = threading.Thread(target=self._watch, args=(self.done,), name='jarvis-video', daemon=True)
                self.watcher.start()
                print(f'[VIDÉO] Destination : {self.target}', flush=True)
                return self._result('RECORDING_START', True,
                    f'Sélectionne la cible dans Spectacle. La session vidéo s’arrêtera au plus tard dans {duration} secondes. Dis « arrête la vidéo » pour terminer plus tôt.')
            except (OSError, subprocess.SubprocessError):
                self._terminate_owned()
                self._close_log(failed=True)
                self.process = None
                self.owner = None
                return self._result('RECORDING_START', False, 'Impossible de démarrer la vidéo dans Spectacle.', 'RECORDING_START_FAILED')

    def _close_log(self, *, failed=False):
        if self.log_file is not None:
            if failed:
                self.log_file.seek(0, 2)
                self.log_file.seek(max(0, self.log_file.tell() - 4000))
                detail = self.log_file.read().decode('utf-8', errors='replace').strip()
                if detail:
                    logging.getLogger(__name__).warning('Spectacle : %s', detail)
            self.log_file.close()
            self.log_file = None

    def _terminate_owned(self):
        process = self.process
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)

    def _valid_video(self):
        if not self.target or not self.target.is_file() or self.target.stat().st_size == 0:
            return False
        result = self.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                           '-show_entries', 'stream=codec_type,width,height:format=duration', '-of', 'json', str(self.target)],
                          capture_output=True, text=True, timeout=10, check=False)
        if result.returncode:
            return False
        data = json.loads(result.stdout)
        return (float(data.get('format', {}).get('duration', 0)) > 0
                and any(s.get('codec_type') == 'video' and s.get('width', 0) > 0 and s.get('height', 0) > 0
                        for s in data.get('streams', [])))

    def stop(self):
        with self.lock:
            if self.process is None:
                return self.last or self._result('RECORDING_STOP', True, 'Aucune vidéo en cours.')
            self.done.set()
            graceful = True
            try:
                if self.process.poll() is None:
                    if self.owner and self._owns(self.owner):
                        # activate() termine une vidéo active. Sinon --dbus ne lance aucune capture.
                        self._call(self.owner, '/org/kde/spectacle', 'org.kde.KDBusService.CommandLine',
                                   "['spectacle', '--dbus', '--nonotify']", '', '{}')
                        try:
                            self.process.wait(timeout=20)
                        except subprocess.TimeoutExpired:
                            graceful = False
                            self._terminate_owned()
                    else:
                        graceful = False
                        self._terminate_owned()
                valid = graceful and self.process.returncode == 0 and self._valid_video()
                self.last = self._result('RECORDING_STOP', valid,
                    'Vidéo enregistrée dans le dossier Videos, Jarvis.' if valid else
                    'Session vidéo terminée. Aucun fichier vidéo finalisé n’a pu être validé.',
                    None if valid else 'RECORDING_NOT_SAVED', self.target if valid else None)
            except (OSError, subprocess.SubprocessError, ValueError, TypeError):
                self._terminate_owned()
                self.last = self._result('RECORDING_STOP', False, 'La finalisation de la vidéo a échoué.', 'RECORDING_NOT_SAVED')
            finally:
                self._close_log(failed=self.last is None or not self.last.success)
                self.process = None
                self.owner = None
            if self.last.artifact_path:
                print(f'[VIDÉO] {self.last.artifact_path}', flush=True)
            return self.last

    def status(self):
        with self.lock:
            if self.process is None:
                return self.last or self._result('RECORDING_STATUS', True, 'Aucune vidéo en cours.')
            if self.process.poll() is not None:
                return self.stop()
            remaining = max(0, int(self.deadline - self.clock()))
            return self._result('RECORDING_STATUS', True, f'Session vidéo active, sélection comprise. Arrêt automatique dans {remaining} secondes.')

    def _watch(self, done):
        while not done.wait(.5):
            with self.lock:
                if done is not self.done or self.process is None:
                    return
                if self.process.poll() is None and self.clock() < self.deadline:
                    continue
                result = self.stop()
            print(f'[VIDÉO] {result.message}', flush=True)
            from core.runtime import get_runtime
            runtime = get_runtime()
            if runtime:
                runtime.enqueue('video-' + uuid4().hex, result.message)
            return

    def close(self):
        result = self.stop()
        watcher = self.watcher
        if watcher and watcher is not threading.current_thread():
            watcher.join(timeout=2)
        return result


screen_recorder = ScreenRecorder()
