"""Guided four-sample wake-word test; never changes production."""

from __future__ import annotations

import sys
import time
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pyaudio

from voice.audio_capture import CaptureConfig, analyze_audio
from voice.wake_word_engine import OpenWakeWordDetector

TESTS = ['TEST {i}/5 — dis "Hey Jarvis" (mêmes conditions).'
         for i in range(1, 6)]


def main() -> None:
    config = CaptureConfig(device_index=12, sample_rate=44100, channels=1,
                           sample_width=2, chunk=1024)
    duration = 5.0
    print("=" * 60)
    print("TEST MANUEL WAKE WORD")
    print("=" * 60)
    print(f"Device : {config.device_index} - default")
    print("Rate   : 44100 Hz\nMode   : mono / int16\n")
    for index, instruction in enumerate(TESTS, 1):
        print("\n" + instruction, flush=True)
        print("Dans 3 secondes :", flush=True)
        for value in (3, 2, 1):
            print(f"{value}...", flush=True); time.sleep(1)
        print("🎙️ PARLE MAINTENANT — capture de 5 secondes", flush=True)
        pa = pyaudio.PyAudio(); stream = None
        try:
            stream = pa.open(format=pyaudio.paInt16, channels=1, rate=44100,
                             input=True, input_device_index=config.device_index,
                             frames_per_buffer=config.chunk)
            raw = b"".join(stream.read(config.chunk, exception_on_overflow=False)
                           for _ in range(round(duration * 44100 / config.chunk)))
        finally:
            if stream is not None: stream.stop_stream(); stream.close()
            pa.terminate()
        path = f"/tmp/hey_jarvis_manual_test_{index}.wav"
        with wave.open(path, "wb") as output:
            output.setnchannels(1); output.setsampwidth(2); output.setframerate(44100)
            output.writeframes(raw)
        metrics = analyze_audio(raw, config)
        detector = OpenWakeWordDetector(sample_rate=44100, threshold=0.5)
        best_score, best_time, detections = 0.0, 0.0, {t: 0 for t in (0.50, 0.45, 0.40, 0.35, 0.30)}
        for offset in range(0, len(raw), config.chunk * 2):
            event = detector.detect(raw[offset:offset + config.chunk * 2])
            timestamp = offset / (44100 * 2)
            if event.score > best_score: best_score, best_time = event.score, timestamp
            for threshold in detections:
                if event.score >= threshold: detections[threshold] += 1
        print("[CAPTURE TERMINÉE]", {"wav": path, "rms": round(metrics["rms"], 1),
              "peak": metrics["peak"], "clipping_percent": round(metrics["clipping"], 4),
              "max_score": round(best_score, 6), "timestamp": round(best_time, 3),
              "thresholds": {str(t): {"detected": detections[t] > 0, "detections": detections[t]} for t in detections}})
        print("Lecture possible : pw-play", path)


if __name__ == "__main__":
    main()
