"""Mesure légère du temps de génération vocale."""

import time


def benchmark(engine, text):
    started = time.perf_counter()
    audio_path = engine.generate(text)
    elapsed = time.perf_counter() - started
    return {
        "generation_seconds": elapsed,
        "audio_path": audio_path,
    }
