"""Lecture des fichiers audio générés par le moteur vocal."""

import os
import subprocess


def play(audio_path, cleanup=True):
    """Joue un fichier WAV avec le lecteur disponible sur le système."""
    if not audio_path:
        return False

    try:
        try:
            subprocess.run(["paplay", audio_path], check=True)
        except FileNotFoundError:
            subprocess.run(["aplay", audio_path], check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        print(f"⚠️ Lecture audio indisponible : {error}")
        print(f"Audio disponible : {audio_path}")
        return False
    finally:
        if cleanup:
            try:
                os.remove(audio_path)
            except OSError:
                pass
