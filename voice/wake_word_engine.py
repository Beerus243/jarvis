"""Local streaming wake-word detector, separate from the existing text fallback."""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from pathlib import Path
from enum import Enum
import time

import numpy as np


class VoiceState(str, Enum):
    SLEEPING = "SLEEPING"
    WAKE_WORD_LISTENING = "WAKE_WORD_LISTENING"
    WAKE_DETECTED = "WAKE_DETECTED"
    COMMAND_LISTENING = "COMMAND_LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"


@dataclass(frozen=True)
class WakeDetection:
    detected: bool
    score: float
    model: str
    detected_at: float


def _resample_to_16khz(data: bytes, sample_rate: int) -> np.ndarray:
    samples = np.frombuffer(data, dtype=np.int16)
    if sample_rate == 16000:
        return samples
    if not len(samples):
        return samples
    target_length = max(1, round(len(samples) * 16000 / sample_rate))
    source_x = np.linspace(0.0, 1.0, num=len(samples), endpoint=False)
    target_x = np.linspace(0.0, 1.0, num=target_length, endpoint=False)
    return np.asarray(np.interp(target_x, source_x, samples), dtype=np.int16)


class OpenWakeWordDetector:
    """Wrap openWakeWord while accepting the project's 44.1 kHz PCM chunks."""

    def __init__(
        self,
        model_name: str = "hey_jarvis",
        threshold: float = 0.5,
        sample_rate: int = 44100,
        model=None,
    ):
        if sample_rate <= 0:
            raise ValueError("La fréquence de capture doit être positive")
        if not 0 < threshold <= 1:
            raise ValueError("Le seuil wake word doit être compris entre 0 et 1")
        self.model_name = model_name
        self.threshold = threshold
        self.sample_rate = sample_rate
        self._ready_snapshot = None
        self._model_key = model_name
        if model is None:
            import openwakeword
            from openwakeword.model import Model
            metadata = openwakeword.models.get(model_name)
            if not metadata:
                raise ValueError(f"Modèle wake word indisponible : {model_name}")
            model = Model(wakeword_model_paths=[metadata['model_path']])
            # openWakeWord 0.4 nomme un modèle explicite d'après son fichier.
            self._model_key = Path(metadata['model_path']).stem
            # Le moteur ignore les 5 premières trames et conserve les anciens
            # embeddings lors de reset(). Préparer une fois un état silencieux
            # complet, puis le restaurer sans calcul ni attente sur le micro.
            for _ in range(32):
                model.predict(np.zeros(1280, dtype=np.int16))
            features = {name: deepcopy(getattr(model.preprocessor, name)) for name in (
                'raw_data_buffer', 'melspectrogram_buffer', 'accumulated_samples', 'feature_buffer')}
            # 0.4.0 ne relit que 480 échantillons précédents, 76 trames mel,
            # et la fenêtre d'entrée du modèle. Ne pas recopier dix secondes
            # d'historique silencieux à chaque retour en veille.
            while len(features['raw_data_buffer']) > 480:
                features['raw_data_buffer'].popleft()
            features['melspectrogram_buffer'] = features['melspectrogram_buffer'][-76:].copy()
            context_frames = max(getattr(model, 'model_inputs', {model_name: 16}).values())
            features['feature_buffer'] = features['feature_buffer'][-context_frames:].copy()
            self._ready_snapshot = (
                deepcopy(model.prediction_buffer),
                features,
            )
        if self._model_key not in model.models:
            raise ValueError(f"Modèle wake word indisponible : {model_name}")
        self.model = model
        self._audio_buffer = np.empty(0, dtype=np.int16)

    def reset(self):
        """Discard pending audio and scores before a new wake session."""
        self._audio_buffer = np.empty(0, dtype=np.int16)
        reset = getattr(self.model, "reset", None)
        if reset:
            reset()
        if self._ready_snapshot is not None:
            predictions, features = self._ready_snapshot
            self.model.prediction_buffer = deepcopy(predictions)
            for name, value in features.items():
                setattr(self.model.preprocessor, name, deepcopy(value))

    def detect(self, pcm_chunk: bytes) -> WakeDetection:
        pcm16 = _resample_to_16khz(pcm_chunk, self.sample_rate)
        self._audio_buffer = np.concatenate((self._audio_buffer, pcm16))
        score = 0.0
        while len(self._audio_buffer) >= 1280:
            frame = self._audio_buffer[:1280]
            self._audio_buffer = self._audio_buffer[1280:]
            predictions = self.model.predict(frame)
            score = max(score, float(predictions.get(self._model_key, 0.0)))
        return WakeDetection(
            detected=score >= self.threshold,
            score=score,
            model=self.model_name,
            detected_at=time.monotonic(),
        )


class WakeWordSession:
    """Small state holder for the wake → command hand-off."""

    def __init__(self):
        self.state = VoiceState.SLEEPING
        self.wake_detected_at: float | None = None

    def start(self) -> None:
        self.state = VoiceState.WAKE_WORD_LISTENING

    def accept(self, detection: WakeDetection) -> bool:
        if self.state != VoiceState.WAKE_WORD_LISTENING or not detection.detected:
            return False
        self.wake_detected_at = detection.detected_at
        self.state = VoiceState.WAKE_DETECTED
        return True

    def begin_command(self) -> bool:
        if self.state != VoiceState.WAKE_DETECTED:
            return False
        self.state = VoiceState.COMMAND_LISTENING
        return True

    def timeout(self) -> None:
        self.state = VoiceState.SLEEPING
        self.wake_detected_at = None
