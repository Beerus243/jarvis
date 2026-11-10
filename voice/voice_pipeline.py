"""Coordination minimale entre entrée vocale, cerveau et sortie vocale."""

from __future__ import annotations

import math
import os
import struct
import subprocess
import tempfile
import time
import uuid
import wave
import threading
import queue
from collections import deque

from core.command_session import GOODBYE, is_exit_command
from core.ui_bridge import events as ui_events


class CaptureCancelled(Exception):
    """A UI stop discards this utterance before it can reach the brain."""

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
        self._ui_listen = threading.Event()
        self._ui_cancel = threading.Event()
        self._ui_speech = queue.Queue(maxsize=1)
        self._ui_request_id = None
        self._ui_origin = 'wake_word'
        self._ui_conversation_id = 'default'
        self._ui_speech_request_id = None
        self._ui_speech_conversation_id = 'default'

    def request_ui_listen(self, request_id=None, origin='ui_voice', conversation_id='default'):
        if self.state != VoiceState.WAKE_WORD_LISTENING:
            raise ValueError('Le microphone traite déjà un échange vocal.')
        self._ui_cancel.clear()
        self._ui_request_id = request_id or uuid.uuid4().hex
        self._ui_origin = origin if origin in ui_events.ORIGINS else 'ui_voice'
        self._ui_conversation_id = conversation_id
        self._ui_listen.set()

    def request_ui_stop(self):
        self._ui_listen.clear()
        self._ui_cancel.set()

    def request_ui_speech(self, text, request_id=None, conversation_id='default'):
        """Queue a confirmed UI replay for the microphone-owning loop."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Texte de réponse invalide.')
        if self._ui_speech.full():
            raise ValueError('Une réponse audio est déjà en attente.')
        self._ui_speech_request_id = request_id or uuid.uuid4().hex
        self._ui_speech_conversation_id = conversation_id
        self._ui_speech.put_nowait(text.strip())

    def start(self):
        self._ui_cancel.clear()
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
            self._ui_request_id = uuid.uuid4().hex
            self._ui_origin = 'wake_word'
            self._ui_conversation_id = 'default'
            print("=" * 50)
            print("[WAKE] Jarvis détecté")
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
        ui_events.voice_state("transcribing", "Transcription de la commande vocale")
        ui_events.state("thinking", "Transcription de la commande vocale")
        started = time.monotonic()
        command = None
        response = None
        should_exit = False
        try:
            command = self.stt(audio_data)
            if self._ui_cancel.is_set():
                return {'success': False, 'error': None, 'cancelled': True}
            if not command or not str(command).strip():
                self.session.timeout()
                self.state = self.session.state
                return {"success": False, "error": "Je n’ai pas compris la commande.", "error_code": "UNRECOGNIZED_SPEECH"}
            command = str(command).strip()
            ui_events.publish({'type': 'transcription.updated', 'text': command,
                               'level': 0, 'phase': 'final'})
            print(f"Fabrice > {command}", flush=True)
            from core.command_understanding import normalize_command
            # Google peut transcrire le mot de réveil « est Jarvis » pendant
            # l'échange. Ce n'est pas une question à envoyer au modèle distant.
            if normalize_command(command) in {'jarvis', 'hey jarvis', 'eh jarvis', 'he jarvis', 'est jarvis'}:
                return {'success': True, 'command': command, 'response': None, 'error': None, 'wake_only': True}
            ui_events.command(
                self._ui_request_id or uuid.uuid4().hex,
                self._ui_origin,
                command,
                'received',
            )
            sleeping = normalize_command(command) in {'retour en veille', 'mets toi en veille', 'merci jarvis'}
            should_exit = is_exit_command(command)
            response = 'Je reste disponible.' if sleeping else (GOODBYE if should_exit else self.brain(command))
            self.state = VoiceState.SPEAKING
            self.session.state = self.state
            if response:
                ui_events.state("speaking", "Réponse vocale du Core")
                ui_events.voice_state("speaking", "Réponse vocale du Core")
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
            if sleeping or normalize_command(command) in {'je vais dormir', 'bonne nuit jarvis'}:
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
            ui_events.voice_state("idle", "Commande vocale terminée")
            ui_events.state("idle", "JARVIS prêt")
        return result

    def timeout_command(self):
        self.session.timeout()
        self.state = self.session.state

    def prepare_voice(self, *, announce=True, background=False):
        """Charge la voix ; en session arrière-plan, le micro peut démarrer pendant le chargement."""
        from voice.voice_manager import prepare_voice, prepare_voice_async, speak

        if self.speaker is speak:
            if background:
                prepare_voice_async()
            else:
                prepare_voice()
        if announce and self.speaker('Bonjour Fabrice. Je suis prêt.') is False:
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
                       speech_threshold=120.0, keep_alive=False):
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
        ambient_levels = deque(maxlen=12)

        def open_stream():
            return pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk,
            )

        pipeline = self
        class ObservedStream:
            def __init__(self, microphone):
                self.microphone = microphone
                self.last_level = 0.0

            def read(self, *args, **kwargs):
                if pipeline._ui_cancel.is_set():
                    raise CaptureCancelled()
                pcm = self.microphone.read(*args, **kwargs)
                if pipeline._ui_cancel.is_set():
                    raise CaptureCancelled()
                now = time.monotonic()
                if now - self.last_level >= 0.1:
                    from voice.audio_capture import rms
                    with ui_events.request_scope(pipeline._ui_request_id, pipeline._ui_origin,
                                                 pipeline._ui_conversation_id):
                        ui_events.publish({'type': 'transcription.updated', 'text': '',
                                           'level': min(1.0, rms(pcm) / 8000),
                                           'phase': 'listening'})
                    self.last_level = now
                return pcm

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
            outcomes = []
            def output():
                try:
                    outcomes.append(speak(text, cancel_event=cancelled))
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
                        print('[INTERRUPT] Jarvis détecté : réponse interrompue.', flush=True)
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
            return False if outcomes and outcomes[0] is False else None

        self._speaking_handler = speak_with_interrupt

        try:
            print("JARVIS > Dites « Jarvis », attendez le signal, puis votre commande.", flush=True)
            print("JARVIS > Détection locale ; la commande est transcrite en français par Google (Internet requis).", flush=True)
            while max_cycles is None or cycles < max_cycles:
                self.start()
                if followup:
                    self.state = self.session.state = VoiceState.COMMAND_LISTENING
                else:
                    stream = open_stream()
                    ui_events.set_voice(self)
                    print("JARVIS en veille — micro prêt : dites « Jarvis ».", flush=True)
                next_notification_check = time.monotonic() + 1.0
                while self.state == VoiceState.WAKE_WORD_LISTENING:
                    try:
                        replay = self._ui_speech.get_nowait()
                    except queue.Empty:
                        replay = None
                    if replay:
                        replay_request_id = self._ui_speech_request_id or uuid.uuid4().hex
                        replay_conversation_id = self._ui_speech_conversation_id
                        self._ui_speech_request_id = None
                        with ui_events.request_scope(replay_request_id, 'ui_voice', replay_conversation_id):
                            close_stream()
                            self.state = self.session.state = VoiceState.SPEAKING
                            ui_events.state('speaking', 'Kokoro lit la réponse demandée')
                            ui_events.voice_state('speaking', 'Kokoro lit la réponse demandée')
                            self._interrupted = False
                            try:
                                spoken = speak_with_interrupt(replay)
                            except Exception as error:
                                ui_events.command(replay_request_id, 'ui_voice', replay, 'failed',
                                                  conversation_id=replay_conversation_id, detail=error)
                                ui_events.voice_state('error', str(error))
                                print(f'JARVIS > Synthèse indisponible : {error}', flush=True)
                            else:
                                ui_events.command(
                                    replay_request_id, 'ui_voice', replay,
                                    'failed' if spoken is False else 'completed',
                                    conversation_id=replay_conversation_id,
                                    detail='Synthèse interrompue ou indisponible' if spoken is False else None,
                                )
                            if self._interrupted:
                                self.state = self.session.state = VoiceState.COMMAND_LISTENING
                                break
                            self.state = self.session.state = VoiceState.WAKE_WORD_LISTENING
                            ui_events.state('idle', 'JARVIS prêt')
                            ui_events.voice_state('idle', 'Synthèse terminée')
                            stream = open_stream()
                        continue
                    if self._ui_listen.is_set():
                        self._ui_listen.clear()
                        self.state = self.session.state = VoiceState.COMMAND_LISTENING
                        break
                    pcm = read_live_chunk(stream)
                    from voice.audio_capture import rms
                    level = rms(pcm)
                    if level < 500:
                        ambient_levels.append(level)
                    self.feed_wake_chunk(pcm, feedback=False)
                    if self.state != VoiceState.WAKE_WORD_LISTENING:
                        break
                    from core.runtime import get_runtime
                    runtime = get_runtime()
                    if runtime and time.monotonic() >= next_notification_check:
                        def announce(message):
                            close_stream()
                            print(f"JARVIS > {message}", flush=True)
                            spoken = False
                            try:
                                self._interrupted = False
                                spoken = speak_with_interrupt(message)
                            except Exception as error:
                                print(f'JARVIS > Synthèse indisponible : {error}', flush=True)
                            self.wake_detector.reset()
                            if self._interrupted:
                                self.state = self.session.state = VoiceState.COMMAND_LISTENING
                            return spoken is not False
                        runtime.deliver(announce)
                        next_notification_check = time.monotonic() + 1.0
                        if stream is None and self.state == VoiceState.WAKE_WORD_LISTENING:
                            stream = open_stream()
                            print("JARVIS en veille — micro prêt : dites « Jarvis ».", flush=True)
                close_stream()
                if self.state != VoiceState.COMMAND_LISTENING:
                    continue
                # Fermer/réouvrir élimine l'audio accumulé pendant le signal
                # ou la réponse précédente. Le STT ne reçoit que la commande.
                if not followup or self._interrupted or retry_command:
                    self._play_feedback()
                retry_command = False
                stream = open_stream()
                ui_events.set_voice(self)
                if not self._ui_request_id:
                    self._ui_request_id = uuid.uuid4().hex
                    self._ui_origin = 'wake_word'
                    self._ui_conversation_id = 'default'
                with ui_events.request_scope(self._ui_request_id, self._ui_origin,
                                             self._ui_conversation_id):
                    ui_events.voice_state('listening', 'Le microphone Python écoute votre commande')
                    ui_events.state('listening', 'Le microphone Python écoute votre commande')
                observed_stream = ObservedStream(stream)
                if followup:
                    print("[LISTEN] Micro prêt, tu peux continuer à parler.", flush=True)
                print("[LISTEN] J'écoute votre commande...", flush=True)
                capture = {}
                try:
                    if endpointing:
                        from voice.audio_capture import CaptureConfig, capture_command
                        noise_floor = None
                        if ambient_levels:
                            noise_floor = sorted(ambient_levels)[len(ambient_levels) // 2]
                        capture = capture_command(observed_stream, CaptureConfig(sample_rate=sample_rate, chunk=chunk,
                            device_index=device_index, maximum_duration=command_seconds,
                            minimum_threshold=speech_threshold, silence_duration=silence_seconds,
                            wait_timeout=(followup_seconds or 8.0) if followup else 8.0),
                            noise_floor=noise_floor)
                        print(
                            f"[LISTEN] Seuil parole {capture['threshold']:.0f}, "
                            f"bruit {capture['noise_floor']:.0f}, durée {capture['duration']:.2f}s.",
                            flush=True,
                        )
                        raw_command = capture['audio']
                        if capture.get('limit_reached'):
                            print('[LISTEN] Limite de durée atteinte : commande non exécutée. Reformule après Jarvis, ou augmente --command-seconds.', flush=True)
                            raw_command = b''
                    else:
                        raw_command = b"".join(observed_stream.read(chunk, exception_on_overflow=False)
                            for _ in range(max(1, math.ceil(command_seconds * sample_rate / chunk))))
                except CaptureCancelled:
                    raw_command = b''
                    capture = {'cancelled': True}
                with ui_events.request_scope(self._ui_request_id, self._ui_origin,
                                             self._ui_conversation_id):
                    ui_events.publish({'type': 'transcription.updated', 'text': '',
                                       'level': 0, 'phase': 'cleared'})
                close_stream()
                if not raw_command:
                    if not followup and not (endpointing and capture.get('limit_reached')):
                        print('[LISTEN] Aucune parole détectée. Réessaie après Jarvis.', flush=True)
                    self.timeout_command()
                    ui_events.state("idle", "JARVIS prêt")
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
                    with ui_events.request_scope(self._ui_request_id, self._ui_origin,
                                                 self._ui_conversation_id):
                        result = self.process_command_audio(audio)
                finally:
                    if runtime:
                        runtime.busy.clear()
                if not result.get('wake_only'):
                    self._ui_request_id = None
                    self._ui_origin = 'wake_word'
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
                            message = "Je n'ai pas pu traiter la commande. Réessaie après Jarvis."
                        speak_with_interrupt(message)
                        followup = followup or self._interrupted
                    except Exception:
                        pass
                if result.get("exit") and not keep_alive:
                    break
                if result.get("exit"):
                    print("JARVIS > Service vocal maintenu en veille.", flush=True)
                    followup = False
                # La disponibilité est annoncée à la réouverture effective du
                # flux au tour suivant, jamais avant de préparer le détecteur.
                cycles += 1
            return list(results)
        finally:
            ui_events.set_voice(None)
            self._speaking_handler = None
            self.timeout_command()
            try:
                close_stream()
            finally:
                pa.terminate()
