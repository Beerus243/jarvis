"""Abstraction for future speech-to-text engines."""


class SpeechInput:
    """Interface minimale que Whisper ou un autre STT pourra remplacer."""

    def __init__(self, listener=None):
        self._listener = listener

    def listen(self):
        try:
            if self._listener is None:
                from voice.listen import listen

                result = listen()
            else:
                result = self._listener()
        except Exception as error:
            print(f"⚠️ Entrée vocale indisponible : {error}")
            return None

        if result is None or not str(result).strip():
            return None
        return str(result).strip()
