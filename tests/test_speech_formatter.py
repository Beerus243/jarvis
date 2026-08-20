from voice.speech_formatter import format_for_speech


def test_formats_time_without_changing_normal_text():
    assert format_for_speech("23:42:15") == "23 heures 42 minutes"
    assert format_for_speech("Réponse technique") == "Réponse technique"
