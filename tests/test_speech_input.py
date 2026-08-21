from voice.speech_input import SpeechInput


def test_speech_input_delegates_to_listener():
    assert SpeechInput(lambda: "bonjour").listen() == "bonjour"


def test_speech_input_returns_text():
    assert SpeechInput(lambda: "  bonjour jarvis  ").listen() == "bonjour jarvis"


def test_speech_input_handles_empty_audio():
    assert SpeechInput(lambda: "").listen() is None


def test_speech_input_handles_recognition_error():
    def failing_listener():
        raise RuntimeError("microphone indisponible")

    assert SpeechInput(failing_listener).listen() is None
