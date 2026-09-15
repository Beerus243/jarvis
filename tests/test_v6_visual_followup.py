import base64
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core.vision import service
from core.vision.capture import VisionError
from core.vision.client import GroqVisionClient
from core.vision.commands import VisionRequest, handle_vision_command
from core.vision.context import VisualSession, visual_session

IMAGE = b'\xff\xd8\xfforiginal'


@pytest.fixture
def visual_tools(monkeypatch, tmp_path):
    monkeypatch.setenv('JARVIS_VISION_PROVIDER', 'groq')
    calls = []
    @contextmanager
    def capture(source, **_):
        calls.append(source)
        path = tmp_path / 'capture.jpg'
        path.write_bytes(IMAGE)
        try:
            yield path
        finally:
            path.unlink()
    monkeypatch.setattr(service, 'capture_image', capture)
    client = Mock()
    client.analyze.return_value = 'Une erreur Python.'
    client.analyze_image.return_value = 'Le module manque.'
    monkeypatch.setattr(service, 'GroqVisionClient', lambda: client)
    return client, calls


def test_followup_reuses_image_after_file_deletion(visual_tools, tmp_path):
    client, calls = visual_tools
    assert handle_vision_command('regarde mon écran') == 'Une erreur Python.'
    assert not (tmp_path / 'capture.jpg').exists()
    assert handle_vision_command('explique cette erreur') == 'Le module manque.'
    assert calls == ['screen']
    client.analyze_image.assert_called_once_with(
        IMAGE, 'explique cette erreur', 'screen',
        previous=('regarde mon écran', 'Une erreur Python.'),
    )
    assert visual_session.get().answer == 'Le module manque.'


@pytest.mark.parametrize('source,command', [('screen', 'regarde mon écran'), ('webcam', 'regarde avec ma webcam')])
def test_refresh_uses_same_source_and_replaces_old_context(source, command, visual_tools):
    client, calls = visual_tools
    handle_vision_command(command)
    client.analyze.return_value = 'Une nouvelle vue.'
    assert handle_vision_command('regarde à nouveau') == 'Une nouvelle vue.'
    assert calls == [source, source]
    assert visual_session.get().answer == 'Une nouvelle vue.'
    client.analyze_image.assert_not_called()


def test_new_source_replaces_context(visual_tools):
    handle_vision_command('regarde mon écran')
    handle_vision_command('regarde avec ma webcam')
    handle_vision_command('décris cet objet')
    assert visual_tools[0].analyze_image.call_args.args[2] == 'webcam'


@pytest.mark.parametrize('command', ['oublie ce que tu as vu', 'oublie la dernière image', 'efface le contexte visuel'])
def test_forget_prevents_later_image_reuse(command, visual_tools):
    handle_vision_command('regarde mon écran')
    assert 'effacé' in handle_vision_command(command)
    assert visual_session.get() is None
    assert 'plus d’image' in handle_vision_command('lis ce texte')
    assert 'plus d’image' in handle_vision_command('regarde à nouveau')
    visual_tools[0].analyze_image.assert_not_called()


def test_expiration_does_not_depend_on_a_new_command(monkeypatch):
    timers = []
    def timer(delay, callback, args):
        item = Mock()
        item.fire = lambda: callback(*args)
        timers.append(item)
        return item
    monkeypatch.setattr('core.vision.context.threading.Timer', timer)
    session = VisualSession()
    generation = session.clear()
    assert session.save(generation, IMAGE, 'screen', 'question', 'réponse')
    timers[0].fire()
    assert session._context is None


def test_followup_does_not_extend_image_lifetime():
    now = [10]
    session = VisualSession(ttl=120, clock=lambda: now[0])
    try:
        generation = session.clear()
        session.save(generation, IMAGE, 'screen', 'question', 'réponse')
        now[0] = 129
        assert session.update(generation, 'suivi', 'réponse suivante')
        now[0] = 130
        assert session.get() is None
        assert not session.update(generation, 'trop tard', 'non')
    finally:
        session.clear()


def test_old_expiration_cannot_erase_new_capture():
    session = VisualSession()
    try:
        old = session.clear()
        session.save(old, IMAGE, 'screen', 'ancienne', 'réponse')
        new = session.clear()
        session.save(new, IMAGE, 'webcam', 'nouvelle', 'réponse')
        session._expire(old)
        assert session.get().source == 'webcam'
    finally:
        session.clear()


def test_forget_during_capture_analysis_cannot_restore_image(visual_tools):
    def analysis(*_):
        visual_session.clear()
        return 'Réponse arrivée trop tard.'
    visual_tools[0].analyze.side_effect = analysis
    assert 'écartée' in handle_vision_command('regarde mon écran')
    assert visual_session.get() is None


def test_forget_during_followup_discards_late_answer(visual_tools):
    handle_vision_command('regarde mon écran')
    def analysis(*_, **kwargs):
        visual_session.clear()
        return 'Réponse arrivée trop tard.'
    visual_tools[0].analyze_image.side_effect = analysis
    assert 'effacé' in handle_vision_command('explique cette erreur')
    assert visual_session.get() is None


def test_failed_new_capture_discards_old_context(visual_tools, monkeypatch):
    handle_vision_command('regarde mon écran')
    monkeypatch.setattr(service, 'capture_image', Mock(side_effect=VisionError('caméra occupée')))
    assert handle_vision_command('regarde avec ma webcam') == 'caméra occupée'
    assert visual_session.get() is None


def test_disabled_vision_erases_context_without_upload(visual_tools, monkeypatch):
    handle_vision_command('regarde mon écran')
    monkeypatch.setenv('JARVIS_VISION_PROVIDER', 'disabled')
    assert 'désactivée' in handle_vision_command('explique cette erreur')
    assert visual_session.get() is None
    visual_tools[0].analyze_image.assert_not_called()


@pytest.mark.parametrize('command', ['quelle heure est-il', 'confirme', 'ouvre Firefox',
    'ne lis pas ce texte', 'comment installer Python'])
def test_other_commands_keep_their_normal_route(command, visual_tools):
    handle_vision_command('regarde mon écran')
    assert handle_vision_command(command) is None
    visual_tools[0].analyze_image.assert_not_called()


def test_general_question_with_own_details_does_not_require_an_image():
    assert handle_vision_command('explique cette erreur Python : ModuleNotFoundError') is None


def test_api_receives_same_image_and_only_last_visual_exchange():
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='Réponse'))])
    assert GroqVisionClient(client=client).analyze_image(
        IMAGE, 'lis ce texte', 'screen', previous=('question précédente', 'description précédente')) == 'Réponse'
    messages = client.chat.completions.create.call_args.kwargs['messages']
    assert len(messages) == 4
    assert messages[1]['content'] == 'question précédente'
    assert messages[2]['content'] == 'description précédente'
    assert 'non une vue en direct' in messages[-1]['content'][0]['text']
    url = messages[-1]['content'][1]['image_url']['url']
    assert base64.b64decode(url.split(',')[1]) == IMAGE


from tests.test_main_commands import routed


def test_voice_main_supports_visual_dialogue_and_clears_on_exit(visual_tools, routed, monkeypatch):
    import main
    from voice.voice_pipeline import LocalWakeVoicePipeline
    from voice.wake_word_engine import WakeDetection
    detector = Mock()
    detector.detect.return_value = WakeDetection(True, .9, 'hey_jarvis', 1.)
    commands = iter(['regarde mon écran', 'explique cette erreur', 'regarde à nouveau', 'oublie ce que tu as vu'])
    speaker = Mock(return_value=True)
    pipeline = LocalWakeVoicePipeline(detector, lambda _: next(commands), main.think,
                                      speaker=speaker, feedback=lambda: None)
    def microphone(**_):
        for _ in range(4):
            pipeline.feed_wake_chunk(b'wake')
            assert pipeline.process_command_audio(b'command')['success']
        assert visual_session.get() is None  # L'oubli précède la fermeture de main.
    monkeypatch.setattr(pipeline, 'run_microphone', microphone)
    monkeypatch.setattr(LocalWakeVoicePipeline, 'from_defaults', lambda **_: pipeline)
    assert main.main(['--no-proactive']) == 0
    assert visual_tools[1] == ['screen', 'screen']
    assert visual_tools[0].analyze_image.call_count == 1
    assert visual_session.get() is None
    routed[0].assert_not_called()
    routed[1].assert_not_called()
    assert 'effacé' in speaker.call_args.args[0]


def test_main_exit_clears_context_even_on_exception(monkeypatch):
    import main
    pipeline = Mock()
    def fail(**_):
        generation = visual_session.clear()
        visual_session.save(generation, IMAGE, 'screen', 'question', 'réponse')
        raise KeyboardInterrupt()
    pipeline.run_microphone.side_effect = fail
    monkeypatch.setattr('voice.voice_pipeline.LocalWakeVoicePipeline.from_defaults', lambda **_: pipeline)
    assert main.main(['--no-proactive']) == 0
    assert visual_session.get() is None
