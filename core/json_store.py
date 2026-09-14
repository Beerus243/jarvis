"""Transactions sur les anciens fichiers JSON : verrou puis remplacement atomique."""
from contextlib import contextmanager
from functools import wraps
import fcntl
import json
import os
from pathlib import Path
import tempfile
import threading

_lock = threading.RLock()
_local = threading.local()


@contextmanager
def transaction(path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        held = getattr(_local, 'held', set())
        if path in held:
            yield
            return
        with open(str(path) + '.lock', 'a') as lockfile:
            fcntl.flock(lockfile, fcntl.LOCK_EX)
            _local.held = held | {path}
            try:
                yield
            finally:
                _local.held = held
                fcntl.flock(lockfile, fcntl.LOCK_UN)


def atomic_write(path, value):
    path = Path(path)
    with transaction(path):
        fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as output:
                json.dump(value, output, ensure_ascii=False, indent=4)
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)


def update(path, transform, default=None):
    with transaction(path):
        try:
            value = json.loads(Path(path).read_text(encoding='utf-8'))
        except FileNotFoundError:
            value = {} if default is None else default
        value = transform(value)
        atomic_write(path, value)
        return value


def locked(path_getter):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with transaction(path_getter()):
                return function(*args, **kwargs)
        return wrapped
    return decorate
