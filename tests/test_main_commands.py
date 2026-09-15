"""Contrat d'entrée : le terminal atteint les routes réelles sans effets PC."""

from unittest.mock import Mock

import pytest

import main
from core import brain, orchestrator
from core.command_session import is_exit_command


@pytest.fixture
def routed(monkeypatch, tmp_path):
    context = lambda message: {"message": message, "reference": message, "reference_info": {}}
    monkeypatch.setattr(brain, "build_decision_context", context)
    monkeypatch.setattr(brain, "add_message", lambda *args: None)
    monkeypatch.setattr(brain, "personalize", lambda *args: None)
    monkeypatch.setattr(orchestrator, "build_decision_context", context)
    monkeypatch.setattr(orchestrator._advanced_personality, "analyze_context", lambda *args: None)
    monkeypatch.setattr(orchestrator._advanced_personality, "handle_banter", lambda *args: None)
    monkeypatch.setattr(orchestrator._advanced_personality, "handle_cultural_reference", lambda *args: None)
    monkeypatch.setattr("core.intelligence._pending_context", lambda: None)
    monkeypatch.setattr("core.action_executor.MEMORY_FILE", tmp_path / "user.json")
    monkeypatch.setattr(orchestrator, "record_diagnostic", lambda *args: None)
    monkeypatch.setattr(orchestrator, "clear_diagnostics", lambda: None)
    monkeypatch.setattr(orchestrator, "_ai_fallback", Mock(side_effect=AssertionError("Unexpected AI fallback")))
    monkeypatch.setattr(orchestrator, "_semantic_fallback", Mock(side_effect=AssertionError("Unexpected memory fallback")))
    action = Mock(return_value=(True, "Action reçue"))
    environment = Mock(return_value="Environnement reçu")
    monkeypatch.setattr(orchestrator, "dispatch", action)
    monkeypatch.setattr(orchestrator, "handle_environment_intent", environment)
    monkeypatch.setattr(main, "speak_response", lambda response: None)
    return action, environment


COMMANDS = [
    ("bonjour", "GREETINGS"),
    ("quelle heure est-il", "GET_TIME"),
    ("ouvre chrome", "OPEN_BROWSER"),
    ("ouvre le navigateur", "OPEN_BROWSER"),
    ("ouvre Firefox", {"action": "OPEN_APPLICATION", "target": "firefox"}),
    ("ouvre le terminal", "OPEN_TERMINAL"),
    ("ouvre VS Code", {"action": "OPEN_APPLICATION", "target": "vscode"}),
    ("ouvre Documents", "OPEN_FOLDER"),
    ("ouvre le dossier Jarvis", {"action": "OPEN_FOLDER", "path": "jarvis"}),
    ("ouvre Google", {"action": "OPEN_URL", "url": "https://www.google.com"}),
    ("ouvre https://example.com/Path?q=Test", {"action": "OPEN_URL", "url": "https://example.com/Path?q=Test"}),
    ("ouvre mon projet Jarvis", {"action": "OPEN_PROJECT", "project": "jarvis"}),
    ("liste mes projets", "LIST_PROJECTS"),
    ("ouvre Spotify", "OPEN_SPOTIFY"),
    ("mets du Damso", {"action": "PLAY_MUSIC", "artist": "damso"}),
    ("pause Spotify", {"action": "PAUSE_MUSIC"}),
    ("continue Spotify", {"action": "RESUME_MUSIC"}),
    ("chanson suivante", {"action": "NEXT_TRACK"}),
    ("chanson précédente", {"action": "PREVIOUS_TRACK"}),
    ("mets en pause", {"action": "MEDIA_PAUSE"}),
    ("reprends la musique", {"action": "MEDIA_PLAY"}),
    ("suivant", {"action": "MEDIA_NEXT"}),
    ("précédent", {"action": "MEDIA_PREVIOUS"}),
    ("cherche Python sur internet", {"action": "SEARCH_WEB", "query": "python"}),
    ("cherche Thor sur Wikipédia", {"action": "SEARCH_WIKIPEDIA", "query": "thor"}),
    ("fais une capture d'écran", "SCREENSHOT"),
    ("capture la fenêtre active", {"action": "SCREENSHOT", "scope": "window"}),
    ("capture une zone de l'écran", {"action": "SCREENSHOT", "scope": "region"}),
    ("enregistre mon écran pendant trente secondes", {"action": "RECORDING_START", "scope": "screen", "duration": 30}),
    ("enregistre la fenêtre pendant deux minutes", {"action": "RECORDING_START", "scope": "window", "duration": 120}),
    ("enregistre une zone", {"action": "RECORDING_START", "scope": "region", "duration": 60}),
    ("arrête la vidéo", {"action": "RECORDING_STOP"}),
    ("statut de l'enregistrement", {"action": "RECORDING_STATUS"}),
    ("monte le son", {"action": "VOLUME_UP"}),
    ("baisse le son", {"action": "VOLUME_DOWN"}),
    ("coupe le son", {"action": "VOLUME_MUTE"}),
    ("remets le son", {"action": "VOLUME_UNMUTE"}),
    ("quel est le volume", {"action": "VOLUME_STATUS"}),
    ("mets le volume à 50", {"action": "VOLUME_SET", "value": "50"}),
    ("quel est le statut de la musique", {"action": "MEDIA_STATUS"}),
    ("liste les applications", {"action": "LIST_APPLICATIONS"}),
    ("affiche mes fenêtres", {"action": "WINDOW_LIST"}),
    ("active le Wi-Fi", {"action": "WIFI_ENABLE"}),
    ("active le Bluetooth", {"action": "BLUETOOTH_ENABLE"}),
    ("donne moi l'état de mon pc", {"action": "PC_STATUS"}),
    ("crée un fichier rapport.txt", {"action": "FILE_CREATE", "path": "rapport.txt"}),
    ("ouvre le fichier rapport.txt", {"action": "FILE_OPEN", "path": "rapport.txt"}),
]


@pytest.mark.parametrize("command,expected", COMMANDS)
def test_main_reaches_action_with_parameters(command, expected, routed, monkeypatch):
    entries = iter([command, "quitter"])
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    assert main.main(['--text']) == 0
    routed[0].assert_called_once_with(expected)
    routed[1].assert_not_called()


@pytest.mark.parametrize('command,expected', COMMANDS)
def test_default_main_voice_reaches_same_actions(command, expected, routed, monkeypatch):
    from voice.voice_pipeline import LocalWakeVoicePipeline
    from voice.wake_word_engine import WakeDetection
    detector = Mock()
    detector.detect.return_value = WakeDetection(True, .9, 'hey_jarvis', 1.0)
    speaker = Mock(return_value=True)
    pipeline = LocalWakeVoicePipeline(detector, lambda _: command, main.think,
                                      speaker=speaker, feedback=lambda: None)
    def microphone(**_):
        pipeline.feed_wake_chunk(b'wake')
        assert pipeline.process_command_audio(b'commande')['success']
    monkeypatch.setattr(pipeline, 'run_microphone', microphone)
    monkeypatch.setattr(LocalWakeVoicePipeline, 'from_defaults', lambda **_: pipeline)
    keyboard = Mock(side_effect=AssertionError('Aucune saisie clavier attendue'))
    monkeypatch.setattr('builtins.input', keyboard)
    assert main.main(['--no-proactive']) == 0
    routed[0].assert_called_once_with(expected)
    speaker.assert_any_call('Action reçue')
    keyboard.assert_not_called()


@pytest.mark.parametrize("command,expected", [
    ("vérifie mon environnement", "ENVIRONMENT_AUDIT"),
    ("vérifie Flutter", "FLUTTER_AUDIT"),
    ("vérifie Android", "ANDROID_AUDIT"),
    ("vérifie Java", "JDK_AUDIT"),
    ("qu'est-ce qui manque ?", "ENVIRONMENT_GAPS"),
    ("suis-je prêt pour compiler Flutter Android ?", "FLUTTER_ANDROID_BUILD_CHECK"),
    ("prépare mon environnement Android", "ENVIRONMENT_REPAIR_PLAN"),
    ("installe le JDK", "JDK_INSTALL"),
    ("installe les outils Android", "ANDROID_TOOLS_INSTALL"),
])
def test_main_reaches_environment(command, expected, routed, monkeypatch):
    entries = iter([command, "quitter"])
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    main.main(['--text'])
    routed[1].assert_called_once()
    assert routed[1].call_args.args[0].intent == expected
    routed[0].assert_not_called()


def test_composed_commands_keep_application_targets(routed, monkeypatch):
    entries = iter(["ouvre Firefox et ouvre le terminal", "quitter"])
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    main.main(['--text', '--no-proactive'])
    assert [call.args[0] for call in routed[0].call_args_list] == [
        {"action": "OPEN_APPLICATION", "target": "firefox"}, {"action": "OPEN_TERMINAL"},
    ]


def test_stop_reaches_pending_environment_cancellation(monkeypatch, routed):
    from core.environment import pending_plan
    monkeypatch.setattr(pending_plan, "_pending", None)
    pending_plan.set_pending(object())
    entries = iter(["Stop !", "quitter"])
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    main.main(['--text'])
    assert routed[1].call_args.args[0].intent == "ENVIRONMENT_CANCEL"


@pytest.mark.parametrize("command", ["QUITTER !", "Au revoir.", "Arrête !", "stop", "q"])
def test_normalized_exit_commands(command, monkeypatch):
    monkeypatch.setattr("core.environment.pending_plan.get_pending", lambda: None)
    monkeypatch.setattr("core.task_engine.get_active_task", lambda: None)
    assert is_exit_command(command)
    assert not is_exit_command("arrête la musique")


def test_terminal_eof_exits_cleanly(monkeypatch):
    monkeypatch.setattr("builtins.input", Mock(side_effect=EOFError))
    assert main.main(['--text']) == 0
