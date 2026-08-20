from voice.voice_controller import VoiceController


def test_voice_controller_controls_state():
    controller = VoiceController(lambda text: True)
    assert controller.speak("Bonjour") is True
    assert controller.is_speaking() is False
    assert controller.pause() is True
    assert controller.speak("Pause") is False
    assert controller.resume() is True
