from voice.wake_word import WakeWordDetector


def test_wake_word_variants():
    detector = WakeWordDetector()
    for text in ("Jarvis", "jarvis", "JARVIS", "hé Jarvis", "Hey Jarvis"):
        assert detector.detect(text)


def test_wake_word_avoids_false_positives():
    detector = WakeWordDetector()
    for text in ("jardin", "jar", "service"):
        assert not detector.detect(text)
