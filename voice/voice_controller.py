"""Contrôleur minimal de l'état vocal."""


class VoiceController:
    def __init__(self, speaker=None):
        if speaker is None:
            from voice.voice_manager import speak

            speaker = speak
        self._speaker = speaker
        self._speaking = False
        self._paused = False

    def speak(self, text):
        if self._paused:
            return False
        self._speaking = True
        try:
            return bool(self._speaker(text))
        finally:
            self._speaking = False

    def stop(self):
        self._speaking = False
        return True

    def pause(self):
        self._paused = True
        return True

    def resume(self):
        self._paused = False
        return True

    def is_speaking(self):
        return self._speaking
