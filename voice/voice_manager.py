"""Interface de haut niveau entre JARVIS et le moteur vocal Kokoro."""

import threading
import re

_engine = None
_player = None
_synthesis_lock = threading.Lock()


def _speech_chunks(text, limit=220):
    """Petites portions pour commencer à parler et annuler la suite rapidement."""
    for sentence in re.split(r'(?<=[.!?])\s+|\n+', text):
        remaining = sentence.strip()
        while len(remaining) > limit:
            cut = remaining.rfind(' ', 0, limit + 1)
            cut = cut if cut > 0 else limit
            yield remaining[:cut]
            remaining = remaining[cut:].lstrip()
        if remaining:
            yield remaining


def prepare_voice():
    """Précharge le Kokoro configuré ; le mode vocal exige cette voix existante."""
    global _engine
    from voice.kokoro_engine import get_engine

    _engine = get_engine()
    return _engine


def _get_engine():
    """Charge Kokoro une seule fois, uniquement au premier besoin vocal."""
    global _engine

    if _engine is None:
        try:
            from voice.kokoro_engine import get_engine
            _engine = get_engine()
        except (ImportError, RuntimeError, OSError) as error:
            from voice.fallback_engine import EspeakEngine
            print(f"JARVIS > Synthèse locale de secours (Kokoro : {error}).")
            _engine = EspeakEngine()

    return _engine


def _get_player():
    global _player

    if _player is None:
        from voice.audio_player import play

        _player = play

    return _player


def speak(text, cancel_event=None):
    """Prononce une réponse sans jamais interrompre la réponse texte."""
    if not text or not str(text).strip():
        return False

    try:
        from voice.speech_formatter import format_for_speech

        if cancel_event is not None:
            from voice.audio_player import play_interruptible
            spoken = False
            for chunk in _speech_chunks(format_for_speech(text)):
                # Attente du modèle annulable, même si une ancienne inférence
                # CUDA finit encore son morceau en arrière-plan.
                while not cancel_event.is_set():
                    if _synthesis_lock.acquire(timeout=0.05):
                        break
                else:
                    return False
                try:
                    if cancel_event.is_set():
                        return False
                    audio_path = _get_engine().generate(chunk)
                finally:
                    _synthesis_lock.release()
                # Le lecteur supprime aussi un fichier généré après annulation.
                if not audio_path or not play_interruptible(audio_path, cancel_event):
                    return False
                spoken = True
            return spoken

        with _synthesis_lock:
            audio_path = _get_engine().generate(format_for_speech(text))
        if not audio_path:
            return False
        return bool(_get_player()(audio_path))
    except Exception as error:  # pragma: no cover - dépend du matériel local
        print(f"⚠️ Voix indisponible : {error}")
        return False
