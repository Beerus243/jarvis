from unittest.mock import patch

from voice.audio_player import play


def test_play_uses_paplay_and_cleans_file():
    with patch("voice.audio_player.subprocess.run") as run, \
            patch("voice.audio_player.os.remove") as remove:
        assert play("answer.wav") is True

    run.assert_called_once_with(["paplay", "answer.wav"], check=True)
    remove.assert_called_once_with("answer.wav")


def test_play_falls_back_to_aplay():
    with patch(
        "voice.audio_player.subprocess.run",
        side_effect=[FileNotFoundError, None],
    ) as run, patch("voice.audio_player.os.remove"):
        assert play("answer.wav") is True

    assert run.call_count == 2
    assert run.call_args_list[1].args == (["aplay", "answer.wav"],)
