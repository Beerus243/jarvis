"""Coordination minimale entre entrée vocale, cerveau et sortie vocale."""

from __future__ import annotations

import math
import os
import struct
import subprocess
import tempfile
import time
import wave

from voice.wake_word_engine import VoiceState, WakeWordSession


def play_wake_feedback(duration: float = 0.12, frequency: int = 880) -> bool:
    """Play a short fixed tone through the existing Linux audio players."""
    sample_rate = 44100
    samples = max(1, int(sample_rate * duration))
    pcm = b"".join(
        struct.pack("<h", int(9000 * math.sin(2 * math.pi * frequency * i / sample_rate)))
        for i in range(samples)
    )
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output:
            path = output.name
        with wave.open(path, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(sample_rate)
            output.writeframes(pcm)
        for player in (("pw-play",), ("paplay",), ("aplay",)):
            try:
                subprocess.run(
                    [*player, path], check=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                return True
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        return False
    finally:
        if path:
            try:
                os.remove(path)
            except OSError:
                pass


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


class LocalWakeVoicePipeline:
    """Isolated two-step local wake-word pipeline.

    It is intentionally not wired into ``main.py`` yet. Dependencies are
    injectable so state transitions can be tested without a microphone.
    """

    def __init__(self, wake_detector, stt, brain, speaker=None, feedback=None):
        self.wake_detector = wake_detector
        self.stt = stt
        self.brain = brain
        self.speaker = speaker or (lambda _text: True)
        self.feedback = feedback or play_wake_feedback
        self.session = WakeWordSession()
        self.state = VoiceState.SLEEPING

    def start(self):
        self.session.start()
        self.state = self.session.state

    def feed_wake_chunk(self, chunk: bytes):
        """Feed one PCM chunk; never calls STT while sleeping."""
        if self.state == VoiceState.SLEEPING:
            self.start()
        if self.state != VoiceState.WAKE_WORD_LISTENING:
            return None
        detection = self.wake_detector.detect(chunk)
        if self.session.accept(detection):
            self.state = self.session.state
            print("=" * 50)
            print("[WAKE] Hey Jarvis détecté")
            print(f"score: {detection.score:.3f}")
            print("state: WAKE_DETECTED → COMMAND_LISTENING")
            print("=" * 50)
            self.feedback()
            self.session.begin_command()
            self.state = self.session.state
        return detection

    def process_command_audio(self, audio_data):
        """Transcribe only audio supplied after a successful wake detection."""
        if self.state != VoiceState.COMMAND_LISTENING:
            return {"success": False, "error": "Wake word non détecté"}
        self.state = VoiceState.THINKING
        started = time.monotonic()
        try:
            command = self.stt(audio_data)
            if not command or not str(command).strip():
                self.session.timeout()
                self.state = self.session.state
                return {"success": False, "error": "Commande vide"}
            response = self.brain(str(command).strip())
            self.state = VoiceState.SPEAKING
            if response:
                self.speaker(response)
            result = {
                "success": bool(response),
                "command": str(command).strip(),
                "response": response,
                "elapsed": time.monotonic() - started,
                "error": None if response else "Aucune réponse",
            }
        except Exception as error:
            result = {"success": False, "error": str(error)}
        self.session.timeout()
        self.state = self.session.state
        return result

    def timeout_command(self):
        self.session.timeout()
        self.state = self.session.state

    @classmethod
    def from_defaults(cls):
        """Build the real pipeline dependencies lazily for ``--voice``."""
        import speech_recognition as sr

        from core.brain import think
        from voice.voice_manager import speak
        from voice.wake_word_engine import OpenWakeWordDetector

        recognizer = sr.Recognizer()
        return cls(
            OpenWakeWordDetector(sample_rate=44100, threshold=0.40),
            lambda audio: recognizer.recognize_google(audio, language="fr-FR"),
            think,
            speaker=speak,
        )

    def run_microphone(self, device_index: int = 12, sample_rate: int = 44100,
                       chunk: int = 1024, command_seconds: float = 5.0,
                       max_cycles: int | None = None):
        """Run the two-step wake → command loop on the real PyAudio stream."""
        import pyaudio
        import speech_recognition as sr

        pa = pyaudio.PyAudio()
        stream = None
        results = []
        cycles = 0
        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk,
            )
            print("JARVIS en veille...", flush=True)
            while max_cycles is None or cycles < max_cycles:
                self.start()
                while self.state == VoiceState.WAKE_WORD_LISTENING:
                    pcm = stream.read(chunk, exception_on_overflow=False)
                    self.feed_wake_chunk(pcm)
                if self.state != VoiceState.COMMAND_LISTENING:
                    continue
                print("[LISTEN] J'écoute votre commande...", flush=True)
                frames = [
                    stream.read(chunk, exception_on_overflow=False)
                    for _ in range(max(1, round(command_seconds * sample_rate / chunk)))
                ]
                audio = sr.AudioData(b"".join(frames), sample_rate, 2)
                result = self.process_command_audio(audio)
                results.append(result)
                if result.get("command", "").casefold().strip() in {
                    "quitter", "quit", "exit", "stop",
                }:
                    break
                print("[SLEEP] Retour en veille", flush=True)
                cycles += 1
            return results
        finally:
            if stream is not None:
                stream.stop_stream()
                stream.close()
            pa.terminate()
