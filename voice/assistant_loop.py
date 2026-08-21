"""Machine à états du mode vocal avec wake word."""

import time
import unicodedata

from voice.wake_word import WakeWordDetector


SLEEPING = "SLEEPING"
LISTENING = "LISTENING"
THINKING = "THINKING"
SPEAKING = "SPEAKING"
STOPPED = "STOPPED"
STOP_WORDS = {"quitter", "arrete", "arrete toi", "stop", "au revoir"}


def _normalize(text):
    value = unicodedata.normalize("NFD", str(text).casefold())
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return " ".join(value.replace("-", " ").split())


class AssistantLoop:
    def __init__(self, listener=None, speaker=None, brain=None,
                 detector=None, retry_delay=0.1):
        self.listener = listener
        self.speaker = speaker
        self.brain = brain
        self.detector = detector or WakeWordDetector()
        self.retry_delay = retry_delay
        self.state = SLEEPING
        self._running = False

    def _listen(self):
        if self.listener is None:
            from voice.speech_input import SpeechInput

            return SpeechInput().listen()
        return self.listener.listen() if hasattr(self.listener, "listen") else self.listener()

    def _think(self, text):
        if self.brain is None:
            from core.brain import think

            return think(text)
        return self.brain(text)

    def _speak(self, response):
        if self.speaker is None:
            from voice.voice_manager import speak

            return speak(response)
        return self.speaker(response)

    def stop(self):
        self._running = False
        self.state = STOPPED

    def run(self, max_cycles=None):
        self._running = True
        cycles = 0
        results = []
        while self._running and (max_cycles is None or cycles < max_cycles):
            try:
                self.state = SLEEPING
                wake_text = self._listen()
            except StopIteration:
                self.stop()
                break
            except Exception:
                time.sleep(self.retry_delay)
                continue

            if not wake_text or not self.detector.detect(wake_text):
                time.sleep(self.retry_delay)
                cycles += 1
                continue

            self.state = LISTENING
            self._speak("Je vous écoute.")
            try:
                command = self._listen()
            except Exception as error:
                results.append({"success": False, "input": None,
                                "response": None, "error": str(error)})
                self.state = SLEEPING
                time.sleep(self.retry_delay)
                cycles += 1
                continue

            if not command or not str(command).strip():
                self.state = SLEEPING
                cycles += 1
                continue

            command = str(command).strip()
            if _normalize(command) in STOP_WORDS:
                self.stop()
                break

            self.state = THINKING
            try:
                response = self._think(command)
                self.state = SPEAKING
                if response:
                    self._speak(response)
                results.append({"success": bool(response), "input": command,
                                "response": response, "error": None if response else "Aucune réponse"})
            except Exception as error:
                results.append({"success": False, "input": command,
                                "response": None, "error": str(error)})
            self.state = SLEEPING
            cycles += 1
        return results
