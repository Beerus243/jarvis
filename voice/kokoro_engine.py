import os
import time
import subprocess
import tempfile

import torch
import soundfile as sf
from kokoro import KPipeline


class KokoroEngine:

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print("========================================")
        print("        JARVIS - MOTEUR VOCAL")
        print("========================================")
        print(f"Device : {self.device}")

        if self.device == "cuda":
            print(f"GPU    : {torch.cuda.get_device_name(0)}")
            print(f"CUDA   : {torch.version.cuda}")

        print("Chargement de Kokoro...")

        self.pipeline = KPipeline(
            lang_code="f",
            device=self.device,
        )

        self.voice = "ff_siwis"

        print("✅ Kokoro chargé")
        print(f"✅ Voix : {self.voice}")

    def synthesize(self, text, output_path=None):
        if not text or not text.strip():
            return None

        if output_path is None:
            fd, output_path = tempfile.mkstemp(
                suffix=".wav",
                prefix="jarvis_"
            )
            os.close(fd)

        start = time.perf_counter()

        audio_parts = []

        for _, _, audio in self.pipeline(
            text,
            voice=self.voice
        ):
            audio_parts.append(audio)

        if not audio_parts:
            return None

        # Un seul fichier audio pour toute la réponse
        import numpy as np

        audio = np.concatenate(audio_parts)

        sf.write(
            output_path,
            audio,
            24000
        )

        elapsed = time.perf_counter() - start
        duration = len(audio) / 24000

        print(
            f"🎙️ {duration:.2f}s audio "
            f"généré en {elapsed:.2f}s"
        )

        return output_path

    def speak(self, text):
        output_path = self.synthesize(text)

        if not output_path:
            return False

        try:
            # PipeWire / PulseAudio
            subprocess.run(
                ["paplay", output_path],
                check=True
            )

        except FileNotFoundError:

            try:
                subprocess.run(
                    ["aplay", output_path],
                    check=True
                )

            except FileNotFoundError:
                print(
                    "⚠️ Aucun lecteur audio trouvé "
                    "(paplay/aplay)."
                )
                print(f"Audio disponible : {output_path}")
                return False

        except subprocess.CalledProcessError as error:
            print(f"⚠️ Erreur lecture audio : {error}")
            print(f"Audio disponible : {output_path}")
            return False

        finally:
            try:
                os.remove(output_path)
            except OSError:
                pass

        return True


# Singleton :
# Kokoro est chargé UNE SEULE FOIS.
_engine = None


def get_engine():
    global _engine

    if _engine is None:
        _engine = KokoroEngine()

    return _engine


def speak(text):
    return get_engine().speak(text)
