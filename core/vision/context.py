"""Une seule image en mémoire vive, avec expiration et oubli explicite."""
from dataclasses import dataclass, replace
import threading
import time

from core.vision.capture import MAX_IMAGE_BYTES


@dataclass(frozen=True)
class VisualContext:
    image: bytes
    source: str
    question: str
    answer: str
    expires_at: float
    generation: int


class VisualSession:
    def __init__(self, ttl=120, clock=time.monotonic):
        self.ttl = ttl
        self.clock = clock
        self._lock = threading.RLock()
        self._context = None
        self._timer = None
        self._generation = 0

    def clear(self):
        with self._lock:
            self._generation += 1
            self._context = None
            if self._timer:
                self._timer.cancel()
                self._timer = None
            return self._generation

    def _expire(self, generation):
        with self._lock:
            if generation == self._generation:
                self.clear()

    def save(self, generation, image, source, question, answer):
        with self._lock:
            if generation != self._generation:
                return False  # Un oubli ou une autre capture a eu lieu entre-temps.
            if not image.startswith(b'\xff\xd8\xff') or len(image) > MAX_IMAGE_BYTES:
                return False
            self._context = VisualContext(image, source, question[:2000], answer[:6000],
                                          self.clock() + self.ttl, generation)
            self._timer = threading.Timer(self.ttl, self._expire, args=(generation,))
            self._timer.daemon = True
            self._timer.start()
            return True

    def get(self):
        with self._lock:
            if self._context and self.clock() >= self._context.expires_at:
                self.clear()
            return self._context

    def update(self, generation, question, answer):
        with self._lock:
            context = self.get()
            if not context or context.generation != generation:
                return False
            self._context = replace(context, question=question[:2000], answer=answer[:6000])
            return True  # Un suivi ne prolonge pas la conservation de l'image.


visual_session = VisualSession()
