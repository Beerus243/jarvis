"""Manual raw microphone comparison; not part of the production pipeline."""

from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pyaudio

from voice.audio_capture import AudioCapture, CaptureConfig


def save_wav(path: str, data: bytes, config: CaptureConfig) -> None:
    with wave.open(path, "wb") as output:
        output.setnchannels(config.channels)
        output.setsampwidth(config.sample_width)
        output.setframerate(config.sample_rate)
        output.writeframes(data)


def capture_direct(config: CaptureConfig, duration: float) -> bytes:
    pa = pyaudio.PyAudio()
    stream = None
    try:
        info = pa.get_device_info_by_index(config.device_index)
        print("DEVICE", info["name"], "index=", config.device_index)
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=config.channels,
            rate=config.sample_rate,
            input=True,
            input_device_index=config.device_index,
            frames_per_buffer=config.chunk,
        )
        return b"".join(
            stream.read(config.chunk, exception_on_overflow=False)
            for _ in range(round(duration * config.sample_rate / config.chunk))
        )
    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        pa.terminate()


def run(label: str, capture, path: str, config: CaptureConfig, duration: float) -> None:
    input(f"{label}: appuie sur Entrée, puis parle pendant {duration:g} secondes... ")
    data = capture()
    save_wav(path, data, config)
    from voice.audio_capture import analyze_audio
    result = analyze_audio(data, config)
    print(label, {
        "rms": round(result["rms"], 1),
        "peak": result["peak"],
        "clipping_percent": round(result["clipping"], 4),
        "duration": round(result["duration"], 3),
        "sample_rate": config.sample_rate,
        "channels": config.channels,
        "path": path,
    })
    print(f"Lecture: pw-play {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=5.0)
    args = parser.parse_args()
    config = CaptureConfig(
        device_index=12,
        sample_rate=44100,
        channels=1,
        sample_width=2,
        chunk=1024,
    )
    run(
        "A PyAudio direct",
        lambda: capture_direct(config, args.duration),
        "/tmp/jarvis_mic_raw_5s.wav",
        config,
        args.duration,
    )
    run(
        "B audio_capture RAW_ONLY",
        lambda: AudioCapture(config).capture_raw(args.duration)["audio"],
        "/tmp/jarvis_mic_raw_audio_capture_5s.wav",
        config,
        args.duration,
    )


if __name__ == "__main__":
    main()
