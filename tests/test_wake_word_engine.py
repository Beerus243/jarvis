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


def test_reset_discards_pending_audio_and_model_scores():
    from unittest.mock import Mock
    model = FakeModel(0.9)
    model.reset = Mock()
    detector = OpenWakeWordDetector(model=model, sample_rate=16000)
    assert not detector.detect(b"\0\0" * 1000).detected
    detector.reset()
    model.reset.assert_called_once()
    assert not detector.detect(b"\0\0" * 1000).detected
    assert detector.detect(b"\0\0" * 280).detected


def test_default_model_is_single_and_ready_immediately_after_reset(monkeypatch):
    import sys
    from collections import deque
    from types import SimpleNamespace
    from unittest.mock import Mock

    class StartupModel:
        def __init__(self, **kwargs):
            self.models = {'hey_jarvis_v0.1': object()}
            self.prediction_buffer = {'hey_jarvis_v0.1': deque(maxlen=30)}
            self.preprocessor = SimpleNamespace(raw_data_buffer=deque(maxlen=160000),
                melspectrogram_buffer=np.zeros((76,32)), accumulated_samples=0,
                feature_buffer=np.zeros((32,96)))
        def reset(self):
            self.prediction_buffer = {'hey_jarvis_v0.1': deque(maxlen=30)}
        def predict(self, audio):
            history = self.prediction_buffer['hey_jarvis_v0.1']
            value = .9 if len(history) >= 5 and np.any(audio) else 0.
            history.append(value)
            self.preprocessor.raw_data_buffer.extend(audio)
            return {'hey_jarvis_v0.1': value}

    factory = Mock(side_effect=StartupModel)
    monkeypatch.setitem(sys.modules, 'openwakeword', SimpleNamespace(
        models={'hey_jarvis': {'model_path': '/models/hey_jarvis_v0.1.onnx'}}))
    monkeypatch.setitem(sys.modules, 'openwakeword.model', SimpleNamespace(Model=factory))
    detector = OpenWakeWordDetector(sample_rate=16000)
    factory.assert_called_once_with(wakeword_model_paths=['/models/hey_jarvis_v0.1.onnx'])
    for _ in range(2):
        detector.model.preprocessor.feature_buffer[:] = 123
        detector.reset()
        assert not np.any(detector.model.preprocessor.feature_buffer)
        assert not any(detector.model.preprocessor.raw_data_buffer)
        # La première trame réelle n'est plus neutralisée après la veille.
        assert detector.detect(np.ones(1280, dtype=np.int16).tobytes()).detected
