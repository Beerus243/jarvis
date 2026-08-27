import numpy as np

from voice.wake_word_engine import (
    OpenWakeWordDetector,
    VoiceState,
    WakeDetection,
    WakeWordSession,
    _resample_to_16khz,
)


class FakeModel:
    models = {"hey_jarvis": object()}

    def __init__(self, score):
        self.score = score
        self.last_input = None

    def predict(self, audio):
        self.last_input = audio
        return {"hey_jarvis": self.score}


def test_resampling_keeps_pcm_and_target_rate_length():
    data = np.zeros(4410, dtype=np.int16).tobytes()
    assert len(_resample_to_16khz(data, 44100)) == 1600


def test_detector_returns_no_wake_below_threshold():
    detector = OpenWakeWordDetector(model=FakeModel(0.2))
    result = detector.detect(b"\0" * 44100)
    assert result.detected is False
    assert result.score == 0.2


def test_detector_detects_above_threshold():
    detector = OpenWakeWordDetector(threshold=0.5, model=FakeModel(0.8))
    result = detector.detect(b"\0" * 44100)
    assert result.detected is True
    assert result.model == "hey_jarvis"


def test_session_wake_to_command_and_timeout():
    session = WakeWordSession()
    session.start()
    assert session.state == VoiceState.WAKE_WORD_LISTENING
    assert session.accept(WakeDetection(False, 0.1, "hey_jarvis", 1.0)) is False
    assert session.accept(WakeDetection(True, 0.9, "hey_jarvis", 2.0)) is True
    assert session.state == VoiceState.WAKE_DETECTED
    assert session.begin_command() is True
    assert session.state == VoiceState.COMMAND_LISTENING
    session.timeout()
    assert session.state == VoiceState.SLEEPING


def test_session_rejects_wake_in_wrong_state():
    session = WakeWordSession()
    detection = WakeDetection(True, 0.9, "hey_jarvis", 1.0)
    assert session.accept(detection) is False
    assert session.state == VoiceState.SLEEPING
