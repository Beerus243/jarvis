"""Guided two-step wake → command test for a human operator."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pyaudio
import speech_recognition as sr

from voice.voice_pipeline import LocalWakeVoicePipeline
from voice.wake_word_engine import OpenWakeWordDetector, VoiceState


def countdown(text: str) -> None:
    print(text, "\n3...", flush=True); time.sleep(1)
    print("2...", flush=True); time.sleep(1)
    print("1...", flush=True); time.sleep(1)


def main() -> None:
    rate, chunk, device = 44100, 1024, 12
    print("=" * 60, "\nTEST PIPELINE VOCAL\n", "=" * 60, sep="")
    detector = OpenWakeWordDetector(sample_rate=rate, threshold=0.5)
    recognizer = sr.Recognizer()
    pipeline = LocalWakeVoicePipeline(
        detector,
        lambda audio: recognizer.recognize_google(audio, language="fr-FR"),
        lambda command: __import__("core.brain", fromlist=["think"]).think(command),
    )
    pa = pyaudio.PyAudio(); stream = None
    try:
        stream = pa.open(format=pyaudio.paInt16, channels=1, rate=rate,
                         input=True, input_device_index=device,
                         frames_per_buffer=chunk)
        pipeline.start(); countdown("ÉTAPE 1/2 — WAKE WORD\nDans 3 secondes, dis :\n\"Hey Jarvis\"")
        deadline = time.monotonic() + 8; max_score = 0.0
        while time.monotonic() < deadline and pipeline.state == VoiceState.WAKE_WORD_LISTENING:
            event = pipeline.feed_wake_chunk(stream.read(chunk, exception_on_overflow=False))
            if event: max_score = max(max_score, event.score)
        if pipeline.state != VoiceState.COMMAND_LISTENING:
            print("Wake non détecté. Score maximal :", round(max_score, 4)); return
        countdown("\nÉTAPE 2/2 — COMMANDE\nDans 3 secondes, dis ta commande")
        print("🎙️ PARLE MAINTENANT :", flush=True)
        raw = b"".join(stream.read(chunk, exception_on_overflow=False)
                       for _ in range(round(5 * rate / chunk)))
        result = pipeline.process_command_audio(sr.AudioData(raw, rate, 2))
        print("STT :", result.get("command"), "\nRésultat :", result)
        print("Retour en veille.")
    finally:
        if stream is not None: stream.stop_stream(); stream.close()
        pa.terminate()


if __name__ == "__main__":
    main()
