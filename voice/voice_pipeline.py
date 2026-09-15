"""Coordination minimale entre entrée vocale, cerveau et sortie vocale."""

from __future__ import annotations

import math
import os
import struct
import subprocess
import tempfile
import time
import wave
import threading
from collections import deque

from core.command_session import GOODBYE, is_exit_command
from voice.wake_word_engine import VoiceState, WakeWordSession


def list_microphones():
    """List input devices without loading STT or wake-word models."""
    import pyaudio

    pa = pyaudio.PyAudio()
    try:
        devices = []
        for index in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(index)
            if info.get("maxInputChannels", 0) > 0:
                devices.append({"index": index, "name": info["name"],
                                "sample_rate": int(info["defaultSampleRate"])})
        return devices
    finally:
        pa.terminate()


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
    """Two-step local wake → command pipeline used by ``main.py --voice``."""

    def __init__(self, wake_detector, stt, brain, speaker=None, feedback=None):
        self.wake_detector = wake_detector
        self.stt = stt
        self.brain = brain
        self.speaker = speaker or (lambda _text: True)
        self.feedback = feedback or play_wake_feedback
        self.session = WakeWordSession()
        self.state = VoiceState.SLEEPING
        self._speaking_handler = None
        self._interrupted = False

    def start(self):
        reset = getattr(self.wake_detector, "reset", None)
        if reset:
            reset()
        self.session.start()
        self.state = self.session.state

    def feed_wake_chunk(self, chunk: bytes, *, feedback=True):
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
            if feedback:
                self._play_feedback()
            self.session.begin_command()
            self.state = self.session.state
        return detection

    def _play_feedback(self):
        try:
            self.feedback()
        except Exception as error:
            print(f"JARVIS > Signal sonore indisponible : {error}", flush=True)

    def process_command_audio(self, audio_data):
        """Transcribe only audio supplied after a successful wake detection."""
        if self.state != VoiceState.COMMAND_LISTENING:
            return {"success": False, "error": "Wake word non détecté"}
        self.state = VoiceState.THINKING
        self.session.state = self.state
        started = time.monotonic()
        command = None
        response = None
        should_exit = False
        try:
            command = self.stt(audio_data)
            if not command or not str(command).strip():
                self.session.timeout()
                self.state = self.session.state
                return {"success": False, "error": "Je n’ai pas compris la commande.", "error_code": "UNRECOGNIZED_SPEECH"}
            command = str(command).strip()
            print(f"Fabrice > {command}", flush=True)
            from core.command_understanding import normalize_command
            # Google peut transcrire le mot de réveil « est Jarvis » pendant
            # l'échange. Ce n'est pas une question à envoyer au modèle distant.
            if normalize_command(command) in {'jarvis', 'hey jarvis', 'eh jarvis', 'he jarvis', 'est jarvis'}:
                return {'success': True, 'command': command, 'response': None, 'error': None, 'wake_only': True}
            sleeping = normalize_command(command) in {'retour en veille', 'mets toi en veille', 'merci jarvis'}
            should_exit = is_exit_command(command)
            response = 'Je reste disponible.' if sleeping else (GOODBYE if should_exit else self.brain(command))
            self.state = VoiceState.SPEAKING
            self.session.state = self.state
            if response:
                print(f"JARVIS > {response}", flush=True)
                (self._speaking_handler or self.speaker)(response)
            result = {
                "success": bool(response),
                "command": command,
                "response": response,
                "elapsed": time.monotonic() - started,
                "error": None if response else "Aucune réponse",
                "exit": should_exit,
            }
            if sleeping:
                result['sleep'] = True
        except Exception as error:
            import speech_recognition as sr
            if command is None and isinstance(error, getattr(sr, 'UnknownValueError', ())):
                return {'success': False, 'command': None, 'response': None,
                        'error': 'Je n’ai pas compris la commande.', 'error_code': 'UNRECOGNIZED_SPEECH'}
            if command is None and isinstance(error, getattr(sr, 'RequestError', ())):
                return {'success': False, 'command': None, 'response': None,
                        'error': 'La transcription vocale est indisponible. Vérifie la connexion Internet.',
                        'error_code': 'STT_UNAVAILABLE'}
            result = {"success": False, "command": command, "response": response,
                      "error": str(error) or type(error).__name__, "exit": should_exit}
        finally:
            self.timeout_command()
        return result

    def timeout_command(self):
        self.session.timeout()
        self.state = self.session.state

    def prepare_voice(self):
        """Charge la voix avant l'écoute et annonce oralement la disponibilité."""
        from voice.voice_manager import prepare_voice, speak

        if self.speaker is speak:
            prepare_voice()
        if self.speaker('Bonjour Fabrice. Je suis prêt.') is False:
            raise RuntimeError('La voix Kokoro ne peut pas être lue. Vérifiez la sortie audio.')

    @classmethod
    def from_defaults(cls, *, sample_rate=44100, threshold=0.40):
        """Build the real pipeline dependencies lazily for ``--voice``."""
        import speech_recognition as sr

        from core.command_session import process_command
        from voice.voice_manager import speak
        from voice.wake_word_engine import OpenWakeWordDetector

        recognizer = sr.Recognizer()
        recognizer.operation_timeout = 10
        return cls(
            OpenWakeWordDetector(sample_rate=sample_rate, threshold=threshold),
            lambda audio: recognizer.recognize_google(audio, language="fr-FR"),
            process_command,
            speaker=speak,
        )

    def run_microphone(self, device_index: int | None = None, sample_rate: int = 44100,
                       chunk: int = 1024, command_seconds: float = 20.0,
                       max_cycles: int | None = None, *, endpointing=False,
                       followup_seconds=0.0, barge_in=False, silence_seconds=1.5,
                       speech_threshold=120.0):
        """Run the two-step wake → command loop on the real PyAudio stream."""
        import pyaudio
        import speech_recognition as sr

        if (sample_rate <= 0 or chunk <= 0 or not math.isfinite(command_seconds)
                or command_seconds <= 0 or not math.isfinite(silence_seconds) or silence_seconds <= 0
                or not math.isfinite(speech_threshold) or speech_threshold <= 0):
            raise ValueError("Fréquence, taille des blocs et durée doivent être positives")
        if getattr(self.wake_detector, "sample_rate", sample_rate) != sample_rate:
            raise ValueError("La fréquence du microphone doit correspondre au détecteur")
        pa = pyaudio.PyAudio()
        stream = None
        results = deque(maxlen=100)
        cycles = 0
        followup = False
        retry_command = False
        next_notification_check = 0.0

        def open_stream():
            return pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk,
            )

        def close_stream():
            nonlocal stream
            if stream is not None:
                current, stream = stream, None
                try:
                    current.stop_stream()
                finally:
                    current.close()

        def read_live_chunk(microphone):
            # PortAudio peut conserver de vieilles trames après un ralentissement.
            # Ne pas passer plusieurs secondes à analyser ce retard en veille.
            available = getattr(microphone, 'get_read_available', lambda: 0)()
            keep = max(chunk, int(sample_rate * 0.25))
            if available > max(chunk * 2, int(sample_rate * 0.5)):
                microphone.read(available - keep, exception_on_overflow=False)
                reset = getattr(self.wake_detector, 'reset', None)
                if reset:
                    reset()
            return microphone.read(chunk, exception_on_overflow=False)

        def speak_with_interrupt(text):
            from voice.voice_manager import speak
            if not barge_in or self.speaker is not speak:
                return self.speaker(text)
            cancelled = threading.Event()
            errors = []
            def output():
                try:
                    speak(text, cancel_event=cancelled)
                except Exception as error:
                    errors.append(error)
            worker = threading.Thread(target=output, daemon=True)
            microphone = None
            try:
                self.wake_detector.reset()
                microphone = open_stream()
                worker.start()
                while worker.is_alive():
                    detection = self.wake_detector.detect(read_live_chunk(microphone))
                    if detection.detected:
                        self._interrupted = True
                        cancelled.set()
                        print('[INTERRUPT] Hey Jarvis détecté : réponse interrompue.', flush=True)
                        break
                worker.join(timeout=0.25 if cancelled.is_set() else 3)
            finally:
                cancelled.set()
                if microphone is not None:
                    try:
                        microphone.stop_stream()
                    finally:
                        microphone.close()
            if errors:
                raise errors[0]

        self._speaking_handler = speak_with_interrupt

        try:
            print("JARVIS > Dites « Hey Jarvis », attendez le signal, puis votre commande.", flush=True)
            print("JARVIS > Détection locale ; la commande est transcrite en français par Google (Internet requis).", flush=True)
            while max_cycles is None or cycles < max_cycles:
                self.start()
                if followup:
                    self.state = self.session.state = VoiceState.COMMAND_LISTENING
                else:
                    stream = open_stream()
                    print("JARVIS en veille — micro prêt : dites « Hey Jarvis ».", flush=True)
                next_notification_check = time.monotonic() + 1.0
                while self.state == VoiceState.WAKE_WORD_LISTENING:
                    pcm = read_live_chunk(stream)
                    self.feed_wake_chunk(pcm, feedback=False)
                    if self.state != VoiceState.WAKE_WORD_LISTENING:
                        break
                    from core.runtime import get_runtime
                    runtime = get_runtime()
                    if runtime and time.monotonic() >= next_notification_check:
                        def announce(message):
                            close_stream()
                            print(f"JARVIS > {message}", flush=True)
                            try:
                                self._interrupted = False
                                speak_with_interrupt(message)
                            except Exception as error:
                                print(f'JARVIS > Synthèse indisponible : {error}', flush=True)
                            self.wake_detector.reset()
                            if self._interrupted:
                                self.state = self.session.state = VoiceState.COMMAND_LISTENING
                            return True  # La notification reste lisible si l’audio échoue.
                        runtime.deliver(announce)
                        next_notification_check = time.monotonic() + 1.0
                        if stream is None and self.state == VoiceState.WAKE_WORD_LISTENING:
                            stream = open_stream()
                            print("JARVIS en veille — micro prêt : dites « Hey Jarvis ».", flush=True)
                close_stream()
                if self.state != VoiceState.COMMAND_LISTENING:
                    continue
                # Fermer/réouvrir élimine l'audio accumulé pendant le signal
                # ou la réponse précédente. Le STT ne reçoit que la commande.
                if not followup or self._interrupted or retry_command:
                    self._play_feedback()
                retry_command = False
                stream = open_stream()
                if followup:
                    print("[LISTEN] Micro prêt, tu peux continuer à parler.", flush=True)
                print("[LISTEN] J'écoute votre commande...", flush=True)
                if endpointing:
                    from voice.audio_capture import CaptureConfig, capture_command
                    capture = capture_command(stream, CaptureConfig(sample_rate=sample_rate, chunk=chunk,
                        device_index=device_index, maximum_duration=command_seconds,
                        minimum_threshold=speech_threshold, silence_duration=silence_seconds,
                        wait_timeout=(followup_seconds or 8.0) if followup else 8.0))
                    raw_command = capture['audio']
                    if capture.get('limit_reached'):
                        print('[LISTEN] Limite de durée atteinte : commande non exécutée. Reformule après Hey Jarvis, ou augmente --command-seconds.', flush=True)
                        raw_command = b''
                else:
                    raw_command = b"".join(stream.read(chunk, exception_on_overflow=False)
                        for _ in range(max(1, math.ceil(command_seconds * sample_rate / chunk))))
                close_stream()
                if not raw_command:
                    if not followup and not (endpointing and capture.get('limit_reached')):
                        print('[LISTEN] Aucune parole détectée. Réessaie après Hey Jarvis.', flush=True)
                    self.timeout_command()
                    followup = False
                    cycles += 1
                    continue
                audio = sr.AudioData(raw_command, sample_rate, 2)
                from core.runtime import get_runtime
                runtime = get_runtime()
                if runtime:
                    runtime.busy.set()
                self._interrupted = False
                was_followup = followup
                try:
                    result = self.process_command_audio(audio)
                finally:
                    if runtime:
                        runtime.busy.clear()
                followup = bool(self._interrupted or (followup_seconds and not result.get('sleep') and result.get('success')))
                if result.get('wake_only'):
                    followup = retry_command = True
                results.append(result)
                unclear = result.get('error_code') == 'UNRECOGNIZED_SPEECH'
                if unclear and was_followup:
                    # Une fausse amorce due au bruit pendant les 8 secondes de
                    # suivi ne doit pas déclencher une nouvelle réponse vocale.
                    print('[LISTEN] Aucune commande comprise. Retour en veille.', flush=True)
                elif result.get("error"):
                    print(f"JARVIS > {result['error']}", flush=True)
                    try:
                        if unclear:
                            message = 'Je n’ai pas compris. Répète ta commande après le signal.'
                            followup = retry_command = True
                        elif result.get('error_code') == 'STT_UNAVAILABLE':
                            message = result['error']
                        else:
                            message = "Je n'ai pas pu traiter la commande. Réessaie après Hey Jarvis."
                        speak_with_interrupt(message)
                        followup = followup or self._interrupted
                    except Exception:
                        pass
                if result.get("exit"):
                    break
                # La disponibilité est annoncée à la réouverture effective du
                # flux au tour suivant, jamais avant de préparer le détecteur.
                cycles += 1
            return list(results)
        finally:
            self._speaking_handler = None
            self.timeout_command()
            try:
                close_stream()
            finally:
                pa.terminate()
