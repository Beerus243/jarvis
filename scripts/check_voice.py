"""Diagnostic local borné : micro, modèle Hey Jarvis et génération française."""
import argparse
import json
from pathlib import Path


def check(device=None, sample_rate=44100):
    import pyaudio
    from voice.voice_pipeline import list_microphones
    from voice.wake_word_engine import OpenWakeWordDetector
    from voice.fallback_engine import EspeakEngine
    result = {'devices': list_microphones(), 'microphone': False, 'wake_model': False, 'tts': False, 'errors': []}
    pa = pyaudio.PyAudio()
    stream = None
    try:
        stream = pa.open(format=pyaudio.paInt16, channels=1, rate=sample_rate,
                         input=True, input_device_index=device, frames_per_buffer=1024)
        audio = stream.read(sample_rate // 4, exception_on_overflow=False)
        result['microphone'] = len(audio) == (sample_rate // 4) * 2
    except Exception as error:
        result['errors'].append('Microphone : ' + str(error))
    finally:
        if stream is not None:
            try:
                stream.stop_stream()
            finally:
                stream.close()
        pa.terminate()
    try:
        detector = OpenWakeWordDetector(sample_rate=sample_rate)
        detector.detect(b'\0\0' * sample_rate)
        result['wake_model'] = True
    except Exception as error:
        result['errors'].append('Hey Jarvis : ' + str(error))
    try:
        path = Path(EspeakEngine().generate('Bonjour Fabrice.'))
        try:
            result['tts'] = path.stat().st_size > 44
        finally:
            path.unlink(missing_ok=True)
    except Exception as error:
        result['errors'].append('Synthèse de secours : ' + str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description='Capture 250 ms localement puis les oublie ; aucun envoi ni installation.')
    parser.add_argument('--mic-device', type=int)
    parser.add_argument('--sample-rate', type=int, default=44100)
    args = parser.parse_args()
    result = check(args.mic_device, args.sample_rate)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all(result[key] for key in ('microphone', 'wake_model', 'tts')) else 1


if __name__ == '__main__':
    raise SystemExit(main())
