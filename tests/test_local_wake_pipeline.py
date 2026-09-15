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


# Regression coverage for the production --voice microphone lifecycle.
import sys
from types import SimpleNamespace
from unittest.mock import Mock
import pytest


@pytest.fixture(autouse=True)
def no_real_feedback(monkeypatch):
    monkeypatch.setattr("voice.voice_pipeline.play_wake_feedback", lambda: True)


@pytest.mark.parametrize("command", ["Quitter !", "AU REVOIR.", "Arrête !"])
def test_exit_is_handled_before_brain(command, monkeypatch):
    monkeypatch.setattr("core.environment.pending_plan.get_pending", lambda: None)
    monkeypatch.setattr("core.task_engine.get_active_task", lambda: None)
    brain = Mock()
    pipeline = make_pipeline(stt=lambda _: command, brain=brain)
    pipeline.feed_wake_chunk(b"wake")
    assert pipeline.process_command_audio(b"audio")["exit"] is True
    brain.assert_not_called()
    assert pipeline.state == pipeline.session.state == VoiceState.SLEEPING


@pytest.mark.parametrize("stage", ["stt", "brain", "speaker"])
def test_failure_returns_to_sleep_and_next_command_works(stage):
    pipeline = make_pipeline()
    failing = Mock(side_effect=RuntimeError("unavailable"))
    setattr(pipeline, stage, failing)
    pipeline.feed_wake_chunk(b"wake")
    assert pipeline.process_command_audio(b"audio")["success"] is False
    assert pipeline.state == pipeline.session.state == VoiceState.SLEEPING
    setattr(pipeline, stage, lambda _: "ok")
    pipeline.feed_wake_chunk(b"wake")
    assert pipeline.process_command_audio(b"audio")["success"] is True


def test_empty_command_never_calls_brain():
    brain = Mock()
    pipeline = make_pipeline(stt=lambda _: " ", brain=brain)
    pipeline.feed_wake_chunk(b"wake")
    assert pipeline.process_command_audio(b"audio")["success"] is False
    brain.assert_not_called()
    assert pipeline.state == VoiceState.SLEEPING


def fake_audio(monkeypatch, *, fail_read=False, fail_close=False):
    streams = []

    class Stream:
        closed = False

        def read(self, count, **kwargs):
            if fail_read:
                raise OSError("microphone disconnected")
            return b"\0\0" * count

        def stop_stream(self):
            if fail_close:
                raise OSError("stop failed")

        def close(self):
            self.closed = True

    def open_stream(**kwargs):
        stream = Stream()
        streams.append(stream)
        return stream

    pa = Mock()
    pa.open.side_effect = open_stream
    monkeypatch.setitem(sys.modules, "pyaudio", SimpleNamespace(PyAudio=lambda: pa, paInt16=8))
    monkeypatch.setitem(sys.modules, "speech_recognition", SimpleNamespace(
        AudioData=lambda data, rate, width: (data, rate, width)))
    return pa, streams


def test_microphone_closed_during_feedback_stt_and_response(monkeypatch):
    pa, streams = fake_audio(monkeypatch)
    phases = []

    def assert_closed(phase):
        assert streams and all(stream.closed for stream in streams)
        phases.append(phase)

    def transcribe(audio):
        assert_closed("stt")
        assert audio == (b"\0\0" * 1024, 44100, 2)
        return "quitter"

    pipeline = make_pipeline(stt=transcribe, feedback=lambda: assert_closed("feedback"))
    pipeline.speaker = lambda _: assert_closed("speaker")
    result = pipeline.run_microphone(command_seconds=0.01)
    assert result[0]["exit"] is True
    assert phases == ["feedback", "stt", "speaker"]
    assert len(streams) == 2
    assert all(call.kwargs["input_device_index"] is None for call in pa.open.call_args_list)
    pa.terminate.assert_called_once()


@pytest.mark.parametrize("fail_close", [False, True])
def test_microphone_failure_releases_resources(monkeypatch, fail_close):
    pa, streams = fake_audio(monkeypatch, fail_read=True, fail_close=fail_close)
    pipeline = make_pipeline()
    with pytest.raises(OSError):
        pipeline.run_microphone(max_cycles=1)
    assert streams[0].closed
    pa.terminate.assert_called_once()
    assert pipeline.state == VoiceState.SLEEPING


def test_mic_loop_recovers_after_stt_error(monkeypatch):
    pa, streams = fake_audio(monkeypatch)
    pipeline = make_pipeline(stt=Mock(side_effect=[RuntimeError("network down"), "quitter"]))
    results = pipeline.run_microphone(command_seconds=0.01, max_cycles=2)
    assert results[0]["success"] is False
    assert results[1]["exit"] is True
    assert len(streams) == 4
    assert all(stream.closed for stream in streams)
    pa.terminate.assert_called_once()


def test_wake_discards_old_audio_before_listening(monkeypatch):
    pa, streams = fake_audio(monkeypatch)
    open_original = pa.open.side_effect
    reads = []
    def open_stream(**kwargs):
        stream = open_original(**kwargs)
        stream.get_read_available = lambda: 44100
        read_original = stream.read
        def read(count, **options):
            reads.append(count)
            return read_original(count, **options)
        stream.read = read
        return stream
    pa.open.side_effect = open_stream
    detector = Detector(True)
    detector.reset = Mock()
    pipeline = make_pipeline(detector=detector, stt=lambda _: 'quitter')
    pipeline.run_microphone(command_seconds=.01)
    assert reads[:2] == [44100 - 11025, 1024]
    assert detector.reset.call_count >= 2
    assert all(s.closed for s in streams)


def test_notifications_are_not_polled_for_each_audio_chunk(monkeypatch):
    pa, streams = fake_audio(monkeypatch)
    now = [0.]
    detector = Detector(False)
    def detect(_):
        now[0] += .025
        return WakeDetection(now[0] >= 2.5, .9, 'hey_jarvis', now[0])
    detector.detect = detect
    monkeypatch.setattr('voice.voice_pipeline.time.monotonic', lambda: now[0])
    runtime = Mock()
    monkeypatch.setattr('core.runtime.get_runtime', lambda: runtime)
    pipeline = make_pipeline(detector=detector, stt=lambda _: 'quitter')
    pipeline.run_microphone(command_seconds=.01)
    assert runtime.deliver.call_count == 2  # ~100 blocs audio, deux consultations.


def test_ready_notice_is_after_model_reset_and_microphone_open(monkeypatch, capsys):
    pa, streams = fake_audio(monkeypatch)
    original_open = pa.open.side_effect
    def open_stream(**kwargs):
        assert 'micro prêt' not in capsys.readouterr().out
        return original_open(**kwargs)
    # Contrôle de la première ouverture uniquement.
    pa.open.side_effect = lambda **kwargs: open_stream(**kwargs) if not streams else original_open(**kwargs)
    detector = Detector(True)
    detector.reset = lambda: print('modèle prêt')
    pipeline = make_pipeline(detector=detector, stt=lambda _: 'quitter')
    pipeline.run_microphone(command_seconds=.01)
    assert 'JARVIS en veille — micro prêt' in capsys.readouterr().out


@pytest.mark.parametrize('command', ['Hey Jarvis', 'est Jarvis', 'Jarvis'])
def test_wake_only_during_exchange_does_not_call_brain(command):
    brain = Mock()
    pipeline = make_pipeline(stt=lambda _: command, brain=brain)
    speaker = Mock()
    pipeline.speaker = speaker
    pipeline.feed_wake_chunk(b'wake')
    result = pipeline.process_command_audio(b'pcm')
    assert result['wake_only'] and result['success']
    brain.assert_not_called()
    speaker.assert_not_called()


def test_unknown_speech_in_followup_returns_to_silence(monkeypatch, capsys):
    import speech_recognition as sr
    unknown = sr.UnknownValueError
    pa, streams = fake_audio(monkeypatch)
    sys.modules['speech_recognition'].UnknownValueError = unknown
    monkeypatch.setattr('voice.audio_capture.capture_command', lambda *_: {'audio': b'pcm'})
    pipeline = make_pipeline(stt=Mock(side_effect=['bonjour', unknown()]))
    speaker = Mock(return_value=True)
    pipeline.speaker = speaker
    results = pipeline.run_microphone(endpointing=True, followup_seconds=8, max_cycles=2)
    assert results[1]['error_code'] == 'UNRECOGNIZED_SPEECH'
    speaker.assert_called_once_with('réponse à bonjour')
    output = capsys.readouterr().out
    assert 'UnknownValueError' not in output
    assert 'Retour en veille' in output


def test_unknown_speech_after_wake_allows_one_retry_without_wake(monkeypatch):
    import speech_recognition as sr
    unknown = sr.UnknownValueError
    fake_audio(monkeypatch)
    sys.modules['speech_recognition'].UnknownValueError = unknown
    monkeypatch.setattr('voice.audio_capture.capture_command', lambda *_: {'audio': b'pcm'})
    detector = Detector(True)
    feedback = Mock()
    pipeline = make_pipeline(detector=detector, stt=Mock(side_effect=[unknown(), 'quitter']), feedback=feedback)
    pipeline.speaker = Mock(return_value=True)
    results = pipeline.run_microphone(endpointing=True, max_cycles=2)
    assert results[1]['exit']
    assert detector.calls == 1
    assert feedback.call_count == 2


def test_transcription_network_error_has_actionable_message(monkeypatch):
    import speech_recognition as sr
    pipeline = make_pipeline(stt=Mock(side_effect=sr.RequestError('private transport details')))
    pipeline.feed_wake_chunk(b'wake')
    result = pipeline.process_command_audio(b'pcm')
    assert result['error_code'] == 'STT_UNAVAILABLE'
    assert 'Internet' in result['error']
    assert 'private transport' not in result['error']
