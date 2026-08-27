from voice.voice_pipeline import LocalWakeVoicePipeline
from voice.wake_word_engine import VoiceState, WakeDetection


class Detector:
    def __init__(self, detected=False):
        self.detected = detected
        self.calls = 0

    def detect(self, _chunk):
        self.calls += 1
        return WakeDetection(self.detected, 0.8 if self.detected else 0.1,
                             "hey_jarvis", float(self.calls))


def make_pipeline(detector=None, stt=None, brain=None, feedback=None):
    return LocalWakeVoicePipeline(
        detector or Detector(True),
        stt or (lambda _audio: "ouvre Spotify"),
        brain or (lambda command: f"réponse à {command}"),
        feedback=feedback,
    )


def test_sleeping_does_not_call_stt_without_wake():
    stt_calls = []
    pipeline = make_pipeline(Detector(False), stt=lambda audio: stt_calls.append(audio))
    pipeline.feed_wake_chunk(b"audio")
    assert pipeline.state == VoiceState.WAKE_WORD_LISTENING
    assert pipeline.process_command_audio(b"commande")["success"] is False
    assert stt_calls == []


def test_wake_transitions_to_command_and_feedback():
    feedback = []
    pipeline = make_pipeline(feedback=lambda: feedback.append(True))
    pipeline.feed_wake_chunk(b"audio")
    assert pipeline.state == VoiceState.COMMAND_LISTENING
    assert feedback == [True]


def test_no_wake_does_not_call_default_feedback(monkeypatch):
    feedback = []
    monkeypatch.setattr("voice.voice_pipeline.play_wake_feedback", lambda: feedback.append(True))
    pipeline = make_pipeline(Detector(False), feedback=None)
    pipeline.feed_wake_chunk(b"audio")
    assert feedback == []


def test_wake_calls_default_feedback_once(monkeypatch):
    feedback = []
    monkeypatch.setattr("voice.voice_pipeline.play_wake_feedback", lambda: feedback.append(True))
    pipeline = make_pipeline(Detector(True), feedback=None)
    pipeline.feed_wake_chunk(b"audio")
    pipeline.feed_wake_chunk(b"audio")
    assert feedback == [True]
    assert pipeline.state == VoiceState.COMMAND_LISTENING


def test_command_transitions_thinking_speaking_and_back():
    spoken = []
    pipeline = LocalWakeVoicePipeline(
        Detector(True), lambda _: "ouvre Spotify", lambda _: "ok",
        speaker=spoken.append,
    )
    pipeline.feed_wake_chunk(b"wake")
    result = pipeline.process_command_audio(b"command-only")
    assert result["success"] is True
    assert result["command"] == "ouvre Spotify"
    assert spoken == ["ok"]
    assert pipeline.state == VoiceState.SLEEPING


def test_timeout_returns_to_sleeping():
    pipeline = make_pipeline()
    pipeline.feed_wake_chunk(b"wake")
    assert pipeline.state == VoiceState.COMMAND_LISTENING
    pipeline.timeout_command()
    assert pipeline.state == VoiceState.SLEEPING


def test_command_is_not_sent_before_wake():
    calls = []
    pipeline = make_pipeline(Detector(False), stt=lambda audio: calls.append(audio))
    assert pipeline.process_command_audio(b"ouvre Spotify")["success"] is False
    assert calls == []
