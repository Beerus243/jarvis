from voice.health import check_voice_stack


def test_voice_stack_interfaces_are_available():
    result = check_voice_stack()
    assert result["voice_manager"] is True
    assert result["audio_player"] is True
    assert result["engine_factory"] in (True, False)
