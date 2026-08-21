"""Coordination minimale entre entrée vocale, cerveau et sortie vocale."""


class VoicePipeline:
    def __init__(self, listener=None, speaker=None, brain=None):
        self.listener = listener
        self.speaker = speaker
        self.brain = brain

    def _listen(self):
        if self.listener is None:
            from voice.speech_input import SpeechInput

            return SpeechInput().listen()
        return self.listener.listen() if hasattr(self.listener, "listen") else self.listener()

    def _speak(self, response):
        if self.speaker is None:
            from voice.voice_manager import speak

            return speak(response)
        return self.speaker(response)

    def _think(self, text):
        if self.brain is None:
            from core.brain import think

            return think(text)
        return self.brain(text)

    def process_once(self):
        """Traite une seule phrase et retourne un résultat sérialisable."""
        try:
            text = self._listen()
        except Exception as error:
            return {"success": False, "input": None, "response": None,
                    "error": f"Écoute vocale indisponible : {error}"}

        if text is None or not str(text).strip():
            return {"success": False, "input": None, "response": None,
                    "error": "Aucune parole détectée"}

        text = str(text).strip()
        try:
            response = self._think(text)
        except Exception as error:
            return {"success": False, "input": text, "response": None,
                    "error": f"Erreur du cerveau : {error}"}

        if response is None or not str(response).strip():
            return {"success": False, "input": text, "response": None,
                    "error": "Aucune réponse générée"}

        response = str(response)
        try:
            self._speak(response)
        except Exception as error:
            return {"success": False, "input": text, "response": response,
                    "error": f"Erreur vocale : {error}"}

        return {"success": True, "input": text, "response": response, "error": None}
