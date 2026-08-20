from voice.speech_input import SpeechInput


def test_speech_input_delegates_to_listener():
    assert SpeechInput(lambda: "bonjour").listen() == "bonjour"
