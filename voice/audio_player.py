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


def play_interruptible(audio_path, cancel_event, cleanup=True):
    """Lecture annulable sans signaler d'autres processus de la session audio."""
    if not audio_path:
        return False
    try:
        for command in (("pw-cat", "--playback"), ("paplay",), ("aplay",)):
            if cancel_event.is_set():
                return False
            try:
                process = subprocess.Popen([*command, str(audio_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                continue
            try:
                while process.poll() is None:
                    if cancel_event.wait(0.05):
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=2)
                        return False
                if process.returncode == 0:
                    return True
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=2)
        return False
    finally:
        if cleanup:
            try:
                os.remove(audio_path)
            except OSError:
                pass
