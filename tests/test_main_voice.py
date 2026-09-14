import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import main
from core.command_session import process_command
from voice.voice_pipeline import LocalWakeVoicePipeline, list_microphones


def test_voice_entrypoint_passes_device_and_rate(monkeypatch):
    pipeline = Mock()
    factory = Mock(return_value=pipeline)
    monkeypatch.setattr(LocalWakeVoicePipeline, "from_defaults", factory)
    assert main.main(["--voice", "--mic-device", "3", "--sample-rate", "16000",
                      "--wake-threshold", "0.6", "--command-seconds", "7"]) == 0
    factory.assert_called_once_with(sample_rate=16000, threshold=0.6)
    pipeline.run_microphone.assert_called_once_with(device_index=3, sample_rate=16000, command_seconds=7.0, endpointing=True, followup_seconds=8.0, barge_in=True)


def test_voice_defaults_use_system_microphone(monkeypatch):
    pipeline = Mock()
    monkeypatch.setattr(LocalWakeVoicePipeline, "from_defaults", Mock(return_value=pipeline))
    keyboard = Mock(side_effect=AssertionError('Le mode par défaut ne doit pas lire le clavier'))
    monkeypatch.setattr('builtins.input', keyboard)
    assert main.main([]) == 0
    pipeline.prepare_voice.assert_called_once()
    keyboard.assert_not_called()
    assert pipeline.run_microphone.call_args.kwargs["device_index"] is None


def test_modes_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        main.main(['--text', '--voice'])


def test_voice_startup_failure_never_falls_back_to_keyboard(monkeypatch):
    keyboard = Mock(side_effect=AssertionError('Pas de retour implicite au clavier'))
    monkeypatch.setattr('builtins.input', keyboard)
    pipeline = Mock()
    pipeline.prepare_voice.side_effect = RuntimeError('Kokoro indisponible')
    monkeypatch.setattr(LocalWakeVoicePipeline, 'from_defaults', lambda **_: pipeline)
    assert main.main([]) == 1
    pipeline.run_microphone.assert_not_called()
    keyboard.assert_not_called()


@pytest.mark.parametrize("args", [["--sample-rate", "0"], ["--mic-device", "-1"],
    ["--wake-threshold", "1.1"], ["--wake-threshold", "nan"], ["--command-seconds", "inf"], ["--command-seconds", "-2"]])
def test_invalid_voice_options_are_rejected(args):
    with pytest.raises(SystemExit) as error:
        main.main(["--voice", *args])
    assert error.value.code == 2


def test_missing_voice_dependency_has_clear_error(monkeypatch, capsys):
    monkeypatch.setattr(LocalWakeVoicePipeline, "from_defaults", Mock(side_effect=ImportError("speech_recognition")))
    assert main.main(["--voice"]) == 1
    assert "speech_recognition" in capsys.readouterr().out


def test_default_voice_uses_same_brain_as_terminal(monkeypatch):
    recognizer = Mock()
    monkeypatch.setitem(sys.modules, "speech_recognition", SimpleNamespace(Recognizer=lambda: recognizer))
    detector = Mock()
    monkeypatch.setattr("voice.wake_word_engine.OpenWakeWordDetector", detector)
    pipeline = LocalWakeVoicePipeline.from_defaults(sample_rate=16000, threshold=0.7)
    assert pipeline.brain is main.think is process_command
    detector.assert_called_once_with(sample_rate=16000, threshold=0.7)
    pipeline.stt(b"audio")
    recognizer.recognize_google.assert_called_once_with(b"audio", language="fr-FR")
    assert recognizer.operation_timeout == 10


def test_list_microphones_filters_outputs_and_releases_audio(monkeypatch):
    pa = Mock()
    pa.get_device_count.return_value = 2
    pa.get_device_info_by_index.side_effect = [
        {"name": "Speaker", "maxInputChannels": 0, "defaultSampleRate": 44100},
        {"name": "Mic", "maxInputChannels": 1, "defaultSampleRate": 48000},
    ]
    monkeypatch.setitem(sys.modules, "pyaudio", SimpleNamespace(PyAudio=lambda: pa))
    assert list_microphones() == [{"index": 1, "name": "Mic", "sample_rate": 48000}]
    pa.terminate.assert_called_once()


def test_voice_preparation_uses_configured_engine_and_greets(monkeypatch):
    from voice import voice_manager
    prepare = Mock()
    speaker = Mock(return_value=True)
    monkeypatch.setattr(voice_manager, 'prepare_voice', prepare)
    monkeypatch.setattr(voice_manager, 'speak', speaker)
    pipeline = LocalWakeVoicePipeline(Mock(), Mock(), Mock(), speaker=speaker)
    pipeline.prepare_voice()
    prepare.assert_called_once()
    speaker.assert_called_once_with('Bonjour Fabrice. Je suis prêt.')
