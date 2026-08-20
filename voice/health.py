"""Vérifications non destructives de la pile vocale."""


def check_voice_stack():
    """Vérifie les interfaces sans charger Kokoro ni accéder au matériel."""
    from voice.audio_player import play
    from voice.voice_manager import speak

    try:
        from voice.kokoro_engine import get_engine
    except (ImportError, ModuleNotFoundError):
        get_engine = None

    return {
        "voice_manager": callable(speak),
        "engine_factory": callable(get_engine),
        "audio_player": callable(play),
    }
