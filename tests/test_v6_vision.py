import base64
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import subprocess

import pytest

from core.vision import capture, service
from core.vision.capture import VisionError
from core.vision.client import GroqVisionClient
from core.vision.commands import VisionRequest, parse_vision_request


@pytest.mark.parametrize('command,source', [
    ('Jarvis, regarde mon écran', 'screen'),
    ('Analyse mon écran et explique cette erreur Python', 'screen'),
    ('Lis le texte à l’écran', 'screen'),
    ('Explique cette erreur sur mon écran', 'screen'),
    ('Que vois-tu sur mon écran ?', 'screen'),
    ('Regarde avec ma webcam', 'webcam'),
    ('Décris avec la caméra', 'webcam'),
    ('Que vois-tu devant la webcam ?', 'webcam'),
    ('Décris ce qui est devant ma webcam', 'webcam'),
    ('fais une capture d’écran', None),
    ('ne regarde pas mon écran', None),
    ('demain regarde mon écran', None),
    ('comment analyser mon écran', None),
    ('cherche une webcam sur internet', None),
    ('regarde mon écraniseur', None),
])
def test_only_explicit_vision_requests_match(command, source):
    request = parse_vision_request(command)
    if source is None:
        assert request is None
    else:
        assert request == VisionRequest(source, command)


@pytest.fixture
def fake_capture_tools(monkeypatch, tmp_path):
    original_directory = capture.tempfile.TemporaryDirectory
    monkeypatch.setattr(capture.tempfile, 'TemporaryDirectory',
                        lambda prefix: original_directory(prefix=prefix, dir=tmp_path))
    monkeypatch.setattr(capture.shutil, 'which', lambda _: '/usr/bin/tool')
    screenshot = Mock()
    def screen(destination, **_):
        def snap():
            screenshot()
            path = Path(destination) / 'screenshot.png'
            path.write_bytes(b'png')
            return SimpleNamespace(success=True, artifact_path=str(path))
        return SimpleNamespace(capture=snap)
    monkeypatch.setattr(capture, 'ScreenCapture', screen)
    original_exists = Path.exists
    monkeypatch.setattr(Path, 'exists', lambda p: str(p) == '/dev/video0' or original_exists(p))
    def convert(args, **kwargs):
        assert kwargs['timeout'] == 12
        assert '-frames:v' in args and args[args.index('-frames:v') + 1] == '1'
        Path(args[-1]).write_bytes(b'\xff\xd8\xffimage')
        return SimpleNamespace(returncode=0)
    runner = Mock(side_effect=convert)
    monkeypatch.setattr(capture.subprocess, 'run', runner)
    return screenshot, runner


@pytest.mark.parametrize('source', ['screen', 'webcam'])
@pytest.mark.parametrize('failure', [False, True])
def test_temporary_capture_is_removed_even_if_analysis_fails(source, failure, fake_capture_tools, tmp_path):
    screenshot, runner = fake_capture_tools
    try:
        with capture.capture_image(source) as path:
            assert path.is_file()
            if failure:
                raise VisionError('réseau indisponible')
    except VisionError:
        assert failure
    assert not path.exists()
    assert list(tmp_path.iterdir()) == []
    assert screenshot.call_count == (1 if source == 'screen' else 0)
    runner.assert_called_once()


def test_failed_screenshot_never_sends_an_old_image(monkeypatch, fake_capture_tools, tmp_path):
    monkeypatch.setattr(capture, 'ScreenCapture', lambda **_: SimpleNamespace(
        capture=lambda: SimpleNamespace(success=False, artifact_path=None)))
    with pytest.raises(VisionError, match='capturer ton écran'):
        with capture.capture_image('screen'):
            pytest.fail('Une capture en échec ne doit pas être utilisée')
    fake_capture_tools[1].assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_camera_timeout_cleans_temporary_files(fake_capture_tools, tmp_path):
    fake_capture_tools[1].side_effect = subprocess.TimeoutExpired('ffmpeg', 12)
    with pytest.raises(VisionError, match='délai'):
        with capture.capture_image('webcam'):
            pytest.fail('Une capture expirée ne doit pas être utilisée')
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('device', ['/etc/passwd', '/dev/video0; touch /tmp/example', 'https://example.com'])
def test_camera_device_cannot_be_a_file_url_or_command(device, fake_capture_tools):
    with pytest.raises(VisionError, match='invalide'):
        with capture.capture_image('webcam', camera_device=device):
            pytest.fail('Périphérique non autorisé')
    fake_capture_tools[1].assert_not_called()


def test_missing_camera_has_explicit_error(fake_capture_tools):
    with pytest.raises(VisionError, match='Aucune webcam'):
        with capture.capture_image('webcam', camera_device='/dev/video999999'):
            pytest.fail('La caméra absente ne doit pas être utilisée')


def test_groq_receives_one_image_and_original_question(tmp_path):
    path = tmp_path / 'image.jpg'
    path.write_bytes(b'\xff\xd8\xfftest')
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='Une erreur Python est visible.'))])
    result = GroqVisionClient(client=client, model='vision-test').analyze(path, 'Explique cette erreur', 'screen')
    assert result == 'Une erreur Python est visible.'
    request = client.chat.completions.create.call_args.kwargs
    assert request['model'] == 'vision-test'
    assert len(request['messages']) == 2  # Aucun historique personnel envoyé.
    content = request['messages'][1]['content']
    assert 'Explique cette erreur' in content[0]['text']
    assert base64.b64decode(content[1]['image_url']['url'].split(',')[1]) == path.read_bytes()
    assert 'tools' not in request


@pytest.mark.parametrize('status,expected', [(401, 'accès'), (404, 'modèle'), (429, 'limite'), (500, 'connexion')])
def test_api_errors_do_not_leak_request_data(tmp_path, status, expected):
    path = tmp_path / 'image.jpg'
    path.write_bytes(b'\xff\xd8\xfftest')
    error = RuntimeError('private-image-base64-and-key')
    error.status_code = status
    client = Mock()
    client.chat.completions.create.side_effect = error
    with pytest.raises(VisionError, match=expected) as caught:
        GroqVisionClient(client=client).analyze(path, 'décris', 'screen')
    assert 'private' not in str(caught.value)


@pytest.mark.parametrize('content', [None, '', '   '])
def test_empty_model_response_is_not_a_success(content, tmp_path):
    path = tmp_path / 'image.jpg'
    path.write_bytes(b'\xff\xd8\xfftest')
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    with pytest.raises(VisionError, match='aucune description'):
        GroqVisionClient(client=client).analyze(path, 'décris', 'screen')


def test_invalid_image_never_calls_api(tmp_path):
    path = tmp_path / 'image.jpg'
    path.write_text('not an image')
    client = Mock()
    with pytest.raises(VisionError, match='JPEG'):
        GroqVisionClient(client=client).analyze(path, 'décris', 'screen')
    client.chat.completions.create.assert_not_called()


def test_configuration_is_checked_before_capture(monkeypatch):
    monkeypatch.setenv('JARVIS_VISION_PROVIDER', 'groq')
    monkeypatch.setattr(service, 'GroqVisionClient', Mock(side_effect=VisionError('clé absente')))
    camera = Mock()
    monkeypatch.setattr(service, 'capture_image', camera)
    assert service.analyze_request(VisionRequest('webcam', 'regarde avec ma webcam')) == 'clé absente'
    camera.assert_not_called()


def test_disabled_vision_does_not_capture_or_contact_groq(monkeypatch):
    monkeypatch.setenv('JARVIS_VISION_PROVIDER', 'disabled')
    camera, client = Mock(), Mock()
    monkeypatch.setattr(service, 'capture_image', camera)
    monkeypatch.setattr(service, 'GroqVisionClient', client)
    assert 'pas configurée' in service.analyze_request(VisionRequest('screen', 'regarde mon écran'))
    camera.assert_not_called()
    client.assert_not_called()


# Même fixture que le catalogue de commandes : aucun effet PC ni mémoire réelle.
from tests.test_main_commands import routed


@pytest.mark.parametrize('command,source', [
    ('regarde mon écran', 'screen'), ('regarde avec ma webcam', 'webcam'),
])
def test_default_main_voice_captures_analyzes_and_speaks(command, source, routed, monkeypatch, tmp_path):
    import main
    from voice.voice_pipeline import LocalWakeVoicePipeline
    from voice.wake_word_engine import WakeDetection
    monkeypatch.setenv('JARVIS_VISION_PROVIDER', 'groq')
    path = tmp_path / 'image.jpg'
    path.write_bytes(b'\xff\xd8\xfftest')
    captured = []
    @contextmanager
    def image(source, **_):
        captured.append(source)
        yield path
    monkeypatch.setattr(service, 'capture_image', image)
    client = Mock()
    client.analyze.return_value = 'Je vois une fenêtre de terminal.'
    monkeypatch.setattr(service, 'GroqVisionClient', lambda: client)
    detector = Mock()
    detector.detect.return_value = WakeDetection(True, .9, 'hey_jarvis', 1.0)
    speaker = Mock(return_value=True)
    pipeline = LocalWakeVoicePipeline(detector, lambda _: command, main.think,
                                      speaker=speaker, feedback=lambda: None)
    def microphone(**_):
        pipeline.feed_wake_chunk(b'wake')
        assert pipeline.process_command_audio(b'command')['success']
    monkeypatch.setattr(pipeline, 'run_microphone', microphone)
    monkeypatch.setattr(LocalWakeVoicePipeline, 'from_defaults', lambda **_: pipeline)
    monkeypatch.setattr('builtins.input', Mock(side_effect=AssertionError('Aucun clavier')))
    assert main.main(['--no-proactive']) == 0
    assert captured == [source]
    client.analyze.assert_called_once_with(path, command, source)
    assert speaker.call_args.args == ('Je vois une fenêtre de terminal.',)
    routed[0].assert_not_called()
    routed[1].assert_not_called()
