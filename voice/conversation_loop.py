"""Boucle de conversation vocale indépendante du cerveau."""

import time
import unicodedata
import re


STOP_WORDS = {"quitter", "arrete", "arrete toi", "stop", "au revoir"}


def _normalize(text):
    value = unicodedata.normalize("NFD", str(text).casefold())
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


class VoiceConversation:
    def __init__(self, listener=None, speaker=None, brain=None, retry_delay=0.1):
        self.listener = listener
        self.speaker = speaker
        self.brain = brain
        self.retry_delay = retry_delay
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

    def run(self, max_turns=None):
        self._running = True
        results = []
        turns = 0
        while self._running and (max_turns is None or turns < max_turns):
            try:
                text = self._listen()
            except StopIteration:
                self.stop()
                break
            except Exception as error:
                results.append({"success": False, "input": None,
                                "response": None, "error": str(error)})
                time.sleep(self.retry_delay)
                continue

            if text is None or not str(text).strip():
                time.sleep(self.retry_delay)
                continue

            text = str(text).strip()
            if _normalize(text) in STOP_WORDS:
                self.stop()
                break

            try:
                response = self._think(text)
                if response is None or not str(response).strip():
                    result = {"success": False, "input": text,
                              "response": None, "error": "Aucune réponse générée"}
                else:
                    response = str(response)
                    self._speak(response)
                    result = {"success": True, "input": text,
                              "response": response, "error": None}
            except Exception as error:
                result = {"success": False, "input": text,
                          "response": None, "error": str(error)}
            results.append(result)
            turns += 1
        return results
