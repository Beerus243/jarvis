"""Interface de haut niveau entre JARVIS et le moteur vocal Kokoro."""

_engine = None
_player = None


def _get_engine():
    """Charge Kokoro une seule fois, uniquement au premier besoin vocal."""
    global _engine

    if _engine is None:
        from voice.kokoro_engine import get_engine

        _engine = get_engine()

    return _engine


def _get_player():
    global _player

    if _player is None:
        from voice.audio_player import play

        _player = play

    return _player


def speak(text):
    """Prononce une réponse sans jamais interrompre la réponse texte."""
    if not text or not str(text).strip():
        return False

    try:
        from voice.speech_formatter import format_for_speech

        audio_path = _get_engine().generate(format_for_speech(text))
        if not audio_path:
            return False
        return bool(_get_player()(audio_path))
    except Exception as error:  # pragma: no cover - dépend du matériel local
        print(f"⚠️ Voix indisponible : {error}")
        return False
