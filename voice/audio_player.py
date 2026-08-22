"""Lecture des fichiers audio générés par le moteur vocal."""

import os
import subprocess


def play(audio_path, cleanup=True):
    """Joue un fichier WAV avec le lecteur disponible sur le système."""
    if not audio_path:
        return False

    errors = []
    try:
        players = (
            ("pw-cat", "--playback"),
            ("paplay",),
            ("aplay",),
        )
        for command in players:
            try:
                subprocess.run([*command, audio_path], check=True)
                return True
            except (FileNotFoundError, OSError, subprocess.CalledProcessError) as error:
                errors.append(f"{command[0]}: {error}")

        print(f"⚠️ Lecture audio indisponible : {'; '.join(errors)}")
        print(f"Audio disponible : {audio_path}")
        return False
    finally:
        if cleanup:
            try:
                os.remove(audio_path)
            except OSError:
                pass
