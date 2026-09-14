"""Interface de haut niveau entre JARVIS et le moteur vocal Kokoro."""

import threading

_engine = None
_player = None
_synthesis_lock = threading.Lock()


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

        # Une interruption peut laisser la génération CUDA en cours quelques
        # instants ; ne pas lancer une seconde inférence sur le même modèle.
        with _synthesis_lock:
            if cancel_event is not None and cancel_event.is_set():
                return False
            audio_path = _get_engine().generate(format_for_speech(text))
        if not audio_path:
            return False
        if cancel_event is not None:
            from voice.audio_player import play_interruptible
            return play_interruptible(audio_path, cancel_event)
        return bool(_get_player()(audio_path))
    except Exception as error:  # pragma: no cover - dépend du matériel local
        print(f"⚠️ Voix indisponible : {error}")
        return False
