from unittest.mock import Mock, patch

from voice import audio_player, voice_manager


def test_voice_manager_returns_success():
    engine = Mock()
    engine.generate.return_value = "/tmp/jarvis-test.wav"
    player = Mock(return_value=True)

    with patch.object(voice_manager, "_get_engine", return_value=engine), \
            patch.object(voice_manager, "_get_player", return_value=player):
        assert voice_manager.speak("Bonjour Fabrice") is True

    engine.generate.assert_called_once()
    player.assert_called_once_with("/tmp/jarvis-test.wav")


def test_voice_manager_handles_generation_failure():
    engine = Mock()
    engine.generate.side_effect = RuntimeError("Kokoro indisponible")

    with patch.object(voice_manager, "_get_engine", return_value=engine):
        assert voice_manager.speak("Bonjour Fabrice") is False


def test_audio_player_failure_does_not_crash():
    with patch.object(
        audio_player.subprocess,
        "run",
        side_effect=[FileNotFoundError(), OSError("PulseAudio indisponible"),
                     OSError("ALSA indisponible")],
    ), patch.object(audio_player.os, "remove") as remove:
        assert audio_player.play("/tmp/jarvis-test.wav") is False

    remove.assert_called_once_with("/tmp/jarvis-test.wav")


def test_audio_player_success_cleans_temporary_file():
    with patch.object(audio_player.subprocess, "run"), \
            patch.object(audio_player.os, "remove") as remove:
        assert audio_player.play("/tmp/jarvis-test.wav") is True

    remove.assert_called_once_with("/tmp/jarvis-test.wav")
