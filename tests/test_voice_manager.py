from unittest.mock import Mock, patch

from voice import voice_manager


def setup_function():
    voice_manager._engine = None
    voice_manager._player = None


def test_speak_uses_engine_and_loads_it_once():
    engine = Mock()
    engine.generate.side_effect = ["first.wav", "second.wav"]
    player = Mock(return_value=True)

    with patch("voice.voice_manager._get_engine", return_value=engine), \
            patch("voice.voice_manager._get_player", return_value=player):
        assert voice_manager.speak("Bonjour Fabrice.") is True
        assert voice_manager.speak("Comment allez-vous ?") is True

    assert engine.generate.call_count == 2
    assert player.call_count == 2


def test_speak_keeps_text_flow_when_kokoro_fails(capsys):
    with patch("voice.voice_manager._get_engine", side_effect=RuntimeError("Kokoro indisponible")):
        assert voice_manager.speak("Réponse de JARVIS") is False

    assert "Voix indisponible" in capsys.readouterr().out


def test_speak_ignores_empty_text():
    with patch("voice.voice_manager._get_engine") as get_engine:
        assert voice_manager.speak("   ") is False
        get_engine.assert_not_called()


def test_prepare_voice_uses_existing_kokoro_without_fallback(monkeypatch):
    import sys
    from types import SimpleNamespace
    engine = Mock(voice='ff_siwis')
    factory = Mock(return_value=engine)
    monkeypatch.setitem(sys.modules, 'voice.kokoro_engine', SimpleNamespace(get_engine=factory))
    assert voice_manager.prepare_voice() is engine
    assert voice_manager._engine.voice == 'ff_siwis'


def test_cancelled_speech_skips_synthesis():
    from threading import Event
    cancelled = Event()
    cancelled.set()
    with patch('voice.voice_manager._get_engine') as engine:
        assert voice_manager.speak('Ancienne réponse', cancel_event=cancelled) is False
        engine.assert_not_called()


def test_interruptible_speech_plays_first_part_before_generating_next(monkeypatch):
    from threading import Event
    from types import SimpleNamespace
    events = []
    def generate(text):
        events.append(('generate', text))
        return 'part.wav'
    def play(path, cancelled):
        events.append(('play', path))
        return True
    monkeypatch.setattr(voice_manager, '_get_engine', lambda: SimpleNamespace(generate=generate))
    monkeypatch.setattr('voice.audio_player.play_interruptible', play)
    assert voice_manager.speak('Première phrase. Deuxième phrase.', cancel_event=Event())
    assert [step[0] for step in events] == ['generate', 'play', 'generate', 'play']


def test_interruption_does_not_generate_remaining_answer(monkeypatch):
    from threading import Event
    from types import SimpleNamespace
    cancelled = Event()
    generate = Mock(return_value='part.wav')
    def play(path, event):
        event.set()
        return False
    monkeypatch.setattr(voice_manager, '_get_engine', lambda: SimpleNamespace(generate=generate))
    monkeypatch.setattr('voice.audio_player.play_interruptible', play)
    assert not voice_manager.speak('Première phrase. Ne pas lire la suite.', cancel_event=cancelled)
    generate.assert_called_once_with('Première phrase.')


def test_cancel_during_synthesis_never_plays_late_file(monkeypatch, tmp_path):
    from threading import Event
    from types import SimpleNamespace
    cancelled = Event()
    path = tmp_path/'late.wav'
    def generate(text):
        path.write_bytes(b'wav')
        cancelled.set()
        return str(path)
    spawn = Mock()
    monkeypatch.setattr(voice_manager, '_get_engine', lambda: SimpleNamespace(generate=generate))
    monkeypatch.setattr('voice.audio_player.subprocess.Popen', spawn)
    assert not voice_manager.speak('Ancienne réponse. Suite.', cancel_event=cancelled)
    spawn.assert_not_called()
    assert not path.exists()


def test_speech_chunks_bound_long_paragraph_without_losing_words():
    text = ' '.join(['mot']*500)
    chunks = list(voice_manager._speech_chunks(text))
    assert all(len(chunk) <= 220 for chunk in chunks)
    assert ' '.join(chunks) == text


def test_wait_for_busy_model_can_be_cancelled(monkeypatch):
    from threading import Event, Thread
    cancelled, finished = Event(), Event()
    generate = Mock()
    monkeypatch.setattr(voice_manager, '_get_engine', generate)
    voice_manager._synthesis_lock.acquire()
    worker = Thread(target=lambda: (voice_manager.speak('Réponse', cancel_event=cancelled), finished.set()))
    try:
        worker.start()
        cancelled.set()
        assert finished.wait(1)
        generate.assert_not_called()
    finally:
        voice_manager._synthesis_lock.release()
        worker.join(timeout=2)
