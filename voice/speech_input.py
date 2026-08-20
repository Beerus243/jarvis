"""Abstraction for future speech-to-text engines."""


class SpeechInput:
    """Interface minimale que Whisper ou un autre STT pourra remplacer."""

    def __init__(self, listener=None):
        self._listener = listener

    def listen(self):
        if self._listener is None:
            from voice.listen import listen

            return listen()
        return self._listener()
