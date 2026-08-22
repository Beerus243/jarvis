from unittest.mock import patch

from voice.audio_player import play


def test_play_uses_pw_cat_first_and_cleans_file():
    with patch("voice.audio_player.subprocess.run") as run, \
            patch("voice.audio_player.os.remove") as remove:
        assert play("answer.wav") is True

    run.assert_called_once_with(["pw-cat", "--playback", "answer.wav"], check=True)
    remove.assert_called_once_with("answer.wav")


def test_play_falls_back_to_aplay():
    with patch(
        "voice.audio_player.subprocess.run",
        side_effect=[FileNotFoundError(), FileNotFoundError(), None],
    ) as run, patch("voice.audio_player.os.remove"):
        assert play("answer.wav") is True

    assert run.call_count == 3
    assert run.call_args_list[1].args == ((["paplay", "answer.wav"],),)[0]
    assert run.call_args_list[2].args == ((["aplay", "answer.wav"],),)[0]


def test_play_falls_back_when_paplay_server_rejects_connection():
    from subprocess import CalledProcessError

    with patch(
        "voice.audio_player.subprocess.run",
        side_effect=[CalledProcessError(1, "pw-cat"), CalledProcessError(1, "paplay"), None],
    ) as run, patch("voice.audio_player.os.remove"):
        assert play("answer.wav") is True

    assert run.call_args_list[2].args == (["aplay", "answer.wav"],)


def test_play_returns_false_when_all_players_fail():
    from subprocess import CalledProcessError

    with patch(
        "voice.audio_player.subprocess.run",
        side_effect=[CalledProcessError(1, "pw-cat"),
                     CalledProcessError(1, "paplay"),
                     CalledProcessError(1, "aplay")],
    ), patch("voice.audio_player.os.remove") as remove:
        assert play("answer.wav") is False

    remove.assert_called_once_with("answer.wav")
