import struct
import pytest
from unittest.mock import Mock

from voice.audio_capture import CaptureConfig, capture_command


def test_endpointing_keeps_start_and_stops_on_silence():
    speech = struct.pack('<100h', *([1000]*100))
    silence = b'\0\0'*100
    stream = Mock()
    stream.read.side_effect = [silence, speech, speech, speech, silence, silence]
    cfg = CaptureConfig(sample_rate=1000, chunk=100, start_frames=2, silence_duration=.2,
                        maximum_duration=5, wait_timeout=2, pre_roll=.3)
    capture = capture_command(stream,cfg)
    assert capture['speech_detected']
    assert capture['audio'].count(speech) == 3
    assert stream.read.call_count == 6


def test_silence_times_out_without_stt_audio():
    stream = Mock()
    stream.read.return_value = b'\0\0'*100
    cfg = CaptureConfig(sample_rate=1000,chunk=100,wait_timeout=.3)
    capture = capture_command(stream,cfg)
    assert not capture['speech_detected'] and capture['audio'] == b''
    assert stream.read.call_count == 3


def test_cancelled_audio_does_not_start_player(monkeypatch, tmp_path):
    from threading import Event
    from voice.audio_player import play_interruptible
    path = tmp_path/'voice.wav'; path.write_bytes(b'audio')
    cancelled = Event(); cancelled.set()
    spawn = Mock()
    monkeypatch.setattr('voice.audio_player.subprocess.Popen',spawn)
    assert not play_interruptible(path,cancelled)
    spawn.assert_not_called()
    assert not path.exists()


def test_followup_accepts_confirmation_without_new_wake(monkeypatch, tmp_path):
    from tests.test_local_wake_pipeline import Detector, fake_audio
    from voice.voice_pipeline import LocalWakeVoicePipeline
    from core.pending_action import set_pending
    from core.session_service import handle_message
    pa, streams = fake_audio(monkeypatch)
    monkeypatch.setattr('core.action_executor.MEMORY_FILE', tmp_path/'user.json')
    monkeypatch.setattr('voice.audio_capture.capture_command', lambda *_: {'audio': b'pcm'})
    detector = Detector(True)
    transcriptions = iter(['ferme firefox', 'confirme'])
    dispatcher = Mock(return_value=(True, 'Firefox fermé'))
    def brain(command):
        if command == 'ferme firefox':
            set_pending({'action': 'CLOSE_APPLICATION', 'target': 'firefox'})
            return 'Confirme ?'
        return handle_message(command, dispatcher=dispatcher).message
    pipeline = LocalWakeVoicePipeline(detector, lambda _: next(transcriptions), brain, feedback=lambda: None)
    results = pipeline.run_microphone(endpointing=True, followup_seconds=8, max_cycles=2)
    assert [r['response'] for r in results] == ['Confirme ?', 'Firefox fermé']
    assert detector.calls == 1
    dispatcher.assert_called_once_with({'action': 'CLOSE_APPLICATION', 'target': 'firefox'})
    assert all(stream.closed for stream in streams)
    pa.terminate.assert_called_once()


def test_wake_interrupts_speaking_and_closes_microphone(monkeypatch):
    from tests.test_local_wake_pipeline import Detector, fake_audio
    from voice.voice_pipeline import LocalWakeVoicePipeline
    from threading import Event
    pa, streams = fake_audio(monkeypatch)
    monkeypatch.setattr('voice.audio_capture.capture_command', lambda *_: {'audio': b'pcm'})
    stopped = Event()
    def speaker(_text, cancel_event=None):
        assert cancel_event.wait(2), 'La lecture doit recevoir l’annulation'
        stopped.set()
    monkeypatch.setattr('voice.voice_manager.speak', speaker)
    detector = Detector(True)
    detector.reset = lambda: None
    pipeline = LocalWakeVoicePipeline(detector, lambda _: 'bonjour', lambda _: 'réponse', speaker=speaker, feedback=lambda: None)
    pipeline.run_microphone(endpointing=True, barge_in=True, max_cycles=1)
    assert stopped.is_set() and pipeline._interrupted
    assert all(stream.closed for stream in streams)
    pa.terminate.assert_called_once()


def test_endpointing_keeps_long_sentence_and_a_natural_pause():
    speech = struct.pack('<100h', *([200]*100))
    silence = b'\0\0' * 100
    stream = Mock()
    stream.read.side_effect = [speech]*30 + [silence]*10 + [speech]*40 + [silence]*15
    cfg = CaptureConfig(sample_rate=1000, chunk=100, minimum_threshold=120,
                        silence_duration=1.5, maximum_duration=20, wait_timeout=8)
    result = capture_command(stream, cfg)
    assert result['audio'].count(speech) == 70
    assert not result['limit_reached']
    assert stream.read.call_count == 95


def test_endpointing_keeps_quieter_words_after_start():
    speech = struct.pack('<100h', *([200]*100))
    soft = struct.pack('<100h', *([90]*100))
    silence = b'\0\0' * 100
    stream = Mock()
    stream.read.side_effect = [speech]*2 + [soft]*20 + [silence]*15
    result = capture_command(stream, CaptureConfig(sample_rate=1000, chunk=100,
        minimum_threshold=120, silence_duration=1.5, maximum_duration=20))
    assert result['audio'].count(soft) == 20
    assert not result['limit_reached']


def test_truncated_command_is_not_dispatched(monkeypatch):
    from tests.test_local_wake_pipeline import make_pipeline, fake_audio
    fake_audio(monkeypatch)
    monkeypatch.setattr('voice.audio_capture.capture_command', lambda *_: {'audio': b'partial', 'limit_reached': True})
    transcribe, brain = Mock(), Mock()
    pipeline = make_pipeline(stt=transcribe, brain=brain)
    assert pipeline.run_microphone(endpointing=True, max_cycles=1) == []
    transcribe.assert_not_called()
    brain.assert_not_called()


def test_interruption_plays_feedback_then_accepts_next_command(monkeypatch):
    from tests.test_local_wake_pipeline import Detector, fake_audio
    from voice.voice_pipeline import LocalWakeVoicePipeline
    fake_audio(monkeypatch)
    captures = []
    def capture(_stream, config):
        captures.append(config)
        return {'audio': b'pcm'}
    monkeypatch.setattr('voice.audio_capture.capture_command', capture)
    feedback = Mock()
    def speaker(_text, cancel_event=None):
        assert cancel_event.wait(2)
    monkeypatch.setattr('voice.voice_manager.speak', speaker)
    detector = Detector(True)
    detector.reset = lambda: None
    transcribe = Mock(side_effect=['bonjour', 'quitter'])
    pipeline = LocalWakeVoicePipeline(detector, transcribe, lambda _: 'réponse', speaker=speaker, feedback=feedback)
    results = pipeline.run_microphone(endpointing=True, barge_in=True, max_cycles=2)
    assert len(results) == 2 and results[1]['exit']
    assert feedback.call_count == 2
    assert captures[1].wait_timeout > 0


def test_endpointing_reports_hard_limit_on_continuous_speech():
    stream = Mock()
    stream.read.return_value = struct.pack('<100h', *([500]*100))
    result = capture_command(stream, CaptureConfig(sample_rate=1000, chunk=100,
        minimum_threshold=120, maximum_duration=2, wait_timeout=8))
    assert result['limit_reached']
    assert result['duration'] == 2
    assert stream.read.call_count == 20


@pytest.mark.parametrize('outcome', [None, False])
def test_notification_can_be_interrupted_into_a_command(monkeypatch, outcome):
    from tests.test_local_wake_pipeline import Detector, fake_audio
    from voice.voice_pipeline import LocalWakeVoicePipeline
    from voice.wake_word_engine import WakeDetection
    fake_audio(monkeypatch)
    now, announcing = [0.], [False]
    detector = Detector(False)
    detector.reset = lambda: None
    def detect(_):
        now[0] += .025
        return WakeDetection(announcing[0], .9, 'hey_jarvis', now[0])
    detector.detect = detect
    monkeypatch.setattr('voice.voice_pipeline.time.monotonic', lambda: now[0])
    calls = []
    def speaker(text, cancel_event=None):
        calls.append((text, cancel_event))
        assert cancel_event is not None and cancel_event.wait(2)
        return outcome
    monkeypatch.setattr('voice.voice_manager.speak', speaker)
    runtime = Mock()
    def deliver(sink):
        announcing[0] = True
        result = sink('Un rappel à interrompre.')
        from voice.wake_word_engine import VoiceState
        assert pipeline.state == VoiceState.COMMAND_LISTENING
        return result
    runtime.deliver.side_effect = deliver
    monkeypatch.setattr('core.runtime.get_runtime', lambda: runtime)
    monkeypatch.setattr('voice.audio_capture.capture_command', lambda *_: {'audio': b'pcm'})
    feedback = Mock()
    pipeline = LocalWakeVoicePipeline(detector, lambda _: 'quitter', Mock(), speaker=speaker, feedback=feedback)
    results = pipeline.run_microphone(endpointing=True, barge_in=True, max_cycles=1)
    assert results[0]['exit']
    assert calls[0][0] == 'Un rappel à interrompre.'
    assert all(event is not None and event.is_set() for _, event in calls)
    feedback.assert_called_once()
