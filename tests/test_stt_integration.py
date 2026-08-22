from unittest.mock import patch
from types import SimpleNamespace

from voice.speech_input import SpeechInput


def test_stt_integration_uses_existing_microphone_backend():
    backend = SimpleNamespace(listen=lambda: "quelle heure est-il")
    with patch.dict("sys.modules", {"voice.listen": backend}):
        assert SpeechInput().listen() == "quelle heure est-il"


def test_stt_integration_handles_microphone_failure():
    backend = SimpleNamespace(listen=lambda: (_ for _ in ()).throw(RuntimeError("microphone")))
    with patch.dict("sys.modules", {"voice.listen": backend}):
        assert SpeechInput().listen() is None
