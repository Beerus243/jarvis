from unittest.mock import Mock, patch

from voice import voice_manager


def setup_function():
    voice_manager._engine = None
    voice_manager._player = None


def test_speak_uses_engine_and_loads_it_once():
    engine = Mock()
    engine.generate.side_effect = ["first.wav", "second.wav"]
    player = Mock(return_value=True)

    with patch("voice.voice_manager._get_engine", return_value=engine), \
            patch("voice.voice_manager._get_player", return_value=player):
        assert voice_manager.speak("Bonjour Fabrice.") is True
        assert voice_manager.speak("Comment allez-vous ?") is True

    assert engine.generate.call_count == 2
    assert player.call_count == 2


def test_speak_keeps_text_flow_when_kokoro_fails(capsys):
    with patch("voice.voice_manager._get_engine", side_effect=RuntimeError("Kokoro indisponible")):
        assert voice_manager.speak("Réponse de JARVIS") is False

    assert "Voix indisponible" in capsys.readouterr().out


def test_speak_ignores_empty_text():
    with patch("voice.voice_manager._get_engine") as get_engine:
        assert voice_manager.speak("   ") is False
        get_engine.assert_not_called()
