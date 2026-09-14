import struct
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
