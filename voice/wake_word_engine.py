"""Local streaming wake-word detector, separate from the existing text fallback."""

from __future__ import annotations

from dataclasses import dataclass
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
        self.model_name = model_name
        self.threshold = threshold
        self.sample_rate = sample_rate
        if model is None:
            from openwakeword.model import Model

            model = Model()
        if model_name not in model.models:
            raise ValueError(f"Modèle wake word indisponible : {model_name}")
        self.model = model
        self._audio_buffer = np.empty(0, dtype=np.int16)

    def detect(self, pcm_chunk: bytes) -> WakeDetection:
        pcm16 = _resample_to_16khz(pcm_chunk, self.sample_rate)
        self._audio_buffer = np.concatenate((self._audio_buffer, pcm16))
        score = 0.0
        while len(self._audio_buffer) >= 1280:
            frame = self._audio_buffer[:1280]
            self._audio_buffer = self._audio_buffer[1280:]
            predictions = self.model.predict(frame)
            score = max(score, float(predictions.get(self.model_name, 0.0)))
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
