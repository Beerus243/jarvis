"""Controlled microphone capture, isolated from the production voice pipeline."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
import statistics
import struct
import wave

import pyaudio


@dataclass(frozen=True)
class CaptureConfig:
    sample_rate: int = 44100
    channels: int = 1
    sample_width: int = 2
    chunk: int = 1024
    device_index: int | None = 12
    calibration_duration: float = 0.25
    threshold_multiplier: float = 1.5
    minimum_threshold: float = 300.0
    pre_roll: float = 0.25
    start_frames: int = 2
    silence_duration: float = 0.8
    minimum_speech: float = 0.3
    maximum_duration: float = 8.0
    wait_timeout: float = 5.0


def rms(data: bytes, sample_width: int = 2) -> float:
    if not data:
        return 0.0
    if sample_width != 2:
        raise ValueError("Only 16-bit PCM is supported")
    samples = struct.unpack("<" + "h" * (len(data) // 2), data)
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))


def peak(data: bytes, sample_width: int = 2) -> int:
    if not data:
        return 0
    if sample_width != 2:
        raise ValueError("Only 16-bit PCM is supported")
    samples = struct.unpack("<" + "h" * (len(data) // 2), data)
    return max(abs(sample) for sample in samples)


def clipping_percent(data: bytes, sample_width: int = 2, limit: int = 32760) -> float:
    if not data:
        return 0.0
    if sample_width != 2:
        raise ValueError("Only 16-bit PCM is supported")
    samples = struct.unpack("<" + "h" * (len(data) // 2), data)
    return sum(abs(sample) >= limit for sample in samples) / len(samples) * 100


def analyze_audio(data: bytes, config: CaptureConfig) -> dict:
    samples = len(data) // config.sample_width
    duration = samples / config.sample_rate if config.sample_rate else 0.0
    return {
        "audio": data,
        "duration": duration,
        "rms": rms(data, config.sample_width),
        "peak": peak(data, config.sample_width),
        "clipping": clipping_percent(data, config.sample_width),
        "speech_detected": bool(data),
    }


def calculate_speech_threshold(
    noise_levels: list[float],
    multiplier: float = 1.5,
    minimum_threshold: float = 300.0,
) -> tuple[float, float]:
    """Return a robust noise floor and the corresponding speech threshold."""
    if not noise_levels:
        return minimum_threshold, minimum_threshold
    noise_floor = statistics.median(noise_levels)
    return max(minimum_threshold, noise_floor * multiplier), noise_floor


class AudioCapture:
    """Small energy-based endpointing capture used for experiments."""

    def __init__(self, config: CaptureConfig | None = None, pyaudio_module=None):
        self.config = config or CaptureConfig()
        self._pyaudio = pyaudio_module or pyaudio

    def _read(self, stream, frames: int) -> list[bytes]:
        return [
            stream.read(self.config.chunk, exception_on_overflow=False)
            for _ in range(frames)
        ]

    def capture_raw(self, duration: float = 5.0) -> dict:
        """Capture continuously without calibration, VAD, or endpointing."""
        cfg = self.config
        pa = self._pyaudio.PyAudio()
        stream = None
        try:
            stream = pa.open(
                format=self._pyaudio.paInt16,
                channels=cfg.channels,
                rate=cfg.sample_rate,
                input=True,
                input_device_index=cfg.device_index,
                frames_per_buffer=cfg.chunk,
            )
            frames = self._read(stream, max(1, math.ceil(
                duration * cfg.sample_rate / cfg.chunk
            )))
            return analyze_audio(b"".join(frames), cfg)
        finally:
            if stream is not None:
                stream.stop_stream()
                stream.close()
            pa.terminate()

    def capture(self) -> dict:
        cfg = self.config
        pa = self._pyaudio.PyAudio()
        stream = None
        try:
            stream = pa.open(
                format=self._pyaudio.paInt16,
                channels=cfg.channels,
                rate=cfg.sample_rate,
                input=True,
                input_device_index=cfg.device_index,
                frames_per_buffer=cfg.chunk,
            )
            calibration_frames = max(1, math.ceil(
                cfg.calibration_duration * cfg.sample_rate / cfg.chunk
            ))
            calibration = self._read(stream, calibration_frames)
            calibration_levels = [
                rms(frame, cfg.sample_width) for frame in calibration
            ]
            threshold, noise_floor = calculate_speech_threshold(
                calibration_levels,
                cfg.threshold_multiplier,
                cfg.minimum_threshold,
            )
            pre_roll_frames = max(1, math.ceil(
                cfg.pre_roll * cfg.sample_rate / cfg.chunk
            ))
            silence_frames = max(1, math.ceil(
                cfg.silence_duration * cfg.sample_rate / cfg.chunk
            ))
            max_frames = max(1, math.ceil(
                cfg.maximum_duration * cfg.sample_rate / cfg.chunk
            ))
            max_wait_frames = max(1, math.ceil(
                cfg.wait_timeout * cfg.sample_rate / cfg.chunk
            ))

            ring = deque(calibration, maxlen=pre_roll_frames)
            pending = 0
            waited = 0
            frames: list[bytes] = []
            speech_frames = 0
            silent_frames = 0
            recording = False

            while waited < max_wait_frames:
                frame = stream.read(cfg.chunk, exception_on_overflow=False)
                level = rms(frame, cfg.sample_width)
                ring.append(frame)
                waited += 1
                if not recording:
                    if level > threshold:
                        pending += 1
                    else:
                        pending = 0
                    if pending >= cfg.start_frames:
                        frames = list(ring)
                        recording = True
                        speech_frames = pending
                        silent_frames = 0
                    continue

                frames.append(frame)
                if level > threshold:
                    speech_frames += 1
                    silent_frames = 0
                else:
                    silent_frames += 1
                if len(frames) >= max_frames:
                    break
                speech_duration = speech_frames * cfg.chunk / cfg.sample_rate
                if (
                    silent_frames >= silence_frames
                    and speech_duration >= cfg.minimum_speech
                ):
                    break

            data = b"".join(frames) if recording else b""
            result = analyze_audio(data, cfg)
            result.update({
                "threshold": threshold,
                "noise_rms": noise_floor,
                "noise_floor": noise_floor,
                "speech_detected": recording and bool(data),
            })
            return result
        finally:
            if stream is not None:
                stream.stop_stream()
                stream.close()
            pa.terminate()


def write_wav(path: str, data: bytes, config: CaptureConfig | None = None) -> None:
    cfg = config or CaptureConfig()
    with wave.open(path, "wb") as output:
        output.setnchannels(cfg.channels)
        output.setsampwidth(cfg.sample_width)
        output.setframerate(cfg.sample_rate)
        output.writeframes(data)
