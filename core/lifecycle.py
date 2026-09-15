"""Un seul main.py, y compris lorsque la proactivité est désactivée."""
import fcntl
from core.state_store import get_store


class ApplicationLock:
    def __init__(self):
        self.file = None

    def acquire(self):
        if self.file:
            return True
        path = get_store().path
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(str(path) + '.main.lock', 'a')
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            return False
        self.file = handle
        return True

    def close(self):
        if self.file:
            self.file.close()
            self.file = None
