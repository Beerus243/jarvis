"""Point d'entrée vocal de JARVIS ; clavier facultatif pour le diagnostic."""

import argparse
import math
import signal
import threading
import time

from core.command_session import GOODBYE, is_exit_command, process_command as think
from voice.voice_manager import speak as speak_response

VERSION = "V7.8"
MAX_BACKGROUND_MIC_FAILURES = 5


def show_banner():
    print("================================")
    print(f"          JARVIS {VERSION}")
    print("          Mode Terminal")
    print("================================")
    print("Bonjour Fabrice.")
    print("JARVIS est opérationnel.")
    print("Tapez 'quitter' pour arrêter.\n")


def run_terminal():
    show_banner()
    while True:
        try:
            message = input("Fabrice > ").strip()
            if not message:
                continue
            if is_exit_command(message):
                print(f"JARVIS > {GOODBYE}")
                break
            from core.runtime import get_runtime
            runtime = get_runtime()
            if runtime:
                runtime.busy.set()
            response = think(message)
            if response:
                print(f"JARVIS > {response}")
                speak_response(response)
            else:
                print("JARVIS > Je n'ai pas de réponse.")
        except (KeyboardInterrupt, EOFError):
            print("\nJARVIS > Arrêt demandé. À bientôt, Fabrice.")
            break
        except Exception as error:
            print(f"JARVIS > Une erreur est survenue : {error}")
        finally:
            from core.runtime import get_runtime
            if get_runtime():
                get_runtime().busy.clear()
    return 0


def _positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("La valeur doit être positive.")
    return number


def _device_index(value):
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("L'index du microphone doit être positif ou nul.")
    return number


def _positive_float(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("La valeur doit être positive et finie.")
    return number


def build_parser():
    parser = argparse.ArgumentParser(description="JARVIS : mot d'activation « Jarvis » et Kokoro par défaut ; --text pour le clavier.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--ui-only", action="store_true", help="Core avec interface WebSocket, sans capture vocale.")
    modes.add_argument("--voice", action="store_true", help="Mode vocal (déjà activé par défaut).")
    modes.add_argument("--text", action="store_true", help="Mode clavier explicite pour le diagnostic.")
    modes.add_argument("--list-microphones", action="store_true", help="Afficher les microphones disponibles.")
    parser.add_argument("--mic-device", type=_device_index, default=None, help="Index du microphone (par défaut : celui du système).")
    parser.add_argument("--sample-rate", type=_positive_int, default=44100, help="Fréquence de capture en Hz (44100 par défaut).")
    parser.add_argument("--wake-threshold", type=_positive_float, default=None, help="Seuil de détection entre 0 et 1 (0.40 ; 0.32 en --background).")
    parser.add_argument("--command-seconds", type=_positive_float, default=20.0, help="Durée maximale d'une commande, en secondes (20 par défaut).")
    parser.add_argument("--silence-seconds", type=_positive_float, default=1.5, help="Pause qui termine une phrase, en secondes (1,5 par défaut).")
    parser.add_argument("--speech-threshold", type=_positive_float, default=None, help="Seuil d'énergie de début de parole (120 ; 160 en --background).")
    parser.add_argument("--followup-seconds", type=_positive_float, default=None, help="Attente d'une réponse sans répéter Jarvis (8 ; 20 en --background).")
    parser.add_argument("--raw-capture", action="store_true", help="Capture fixe de diagnostic, sans détection de fin de phrase.")
    parser.add_argument("--no-barge-in", action="store_true", help="Désactiver l'interruption de la voix par Jarvis.")
    parser.add_argument("--no-proactive", action="store_true", help="Désactiver la surveillance et les rappels pour cette session.")
    parser.add_argument("--background", action="store_true", help="Session automatique : sans annonce, voix en parallèle, reprise micro, réglages usage permanent.")
    ui = parser.add_mutually_exclusive_group()
    ui.add_argument("--ui", action="store_true", help="Activer le WebSocket local (automatique en --background).")
    ui.add_argument("--no-ui", action="store_true", help="Désactiver le WebSocket local.")
    return parser


def main(argv=None):
    from core.vision.health import migrate
    parser = build_parser()
    args = parser.parse_args(argv)
    voice_mode = not args.text and not args.list_microphones and not args.ui_only
    if args.ui_only and args.no_ui:
        parser.error("--ui-only est incompatible avec --no-ui.")
    # Usage permanent : détection un peu plus sensible, suivi plus long, moins
    # de fausses captures sur le bruit ambiant pendant l'attente de commande.
    if args.wake_threshold is None:
        args.wake_threshold = 0.32 if args.background else 0.40
    if args.followup_seconds is None:
        args.followup_seconds = 20.0 if args.background else 8.0
    if args.speech_threshold is None:
        args.speech_threshold = 160.0 if args.background else 120.0
    if args.wake_threshold > 1:
        parser.error("--wake-threshold doit être compris entre 0 et 1.")
    from core.runtime import Runtime
    runtime = None
    ui_bridge = None
    from core.lifecycle import ApplicationLock
    app_lock = ApplicationLock()
    old_signal = None
    try:
        if not args.list_microphones:
            if threading.current_thread() is threading.main_thread():
                old_signal = signal.getsignal(signal.SIGTERM)
                def terminate(signum, frame):
                    raise KeyboardInterrupt
                signal.signal(signal.SIGTERM, terminate)
            while not app_lock.acquire():
                if not args.background:
                    print("JARVIS > Une instance est déjà active.")
                    return 0
                time.sleep(30)
        migrate()
        if not args.no_proactive and not args.list_microphones:
            def notify(message):
                print(f"\nJARVIS > {message}", flush=True)
                return True
            runtime = Runtime(notify=None if voice_mode else notify).start()
        if not args.list_microphones and not args.no_ui and (args.ui or args.ui_only or args.background):
            from core.ui_bridge.server import UIBridge
            ui_bridge = UIBridge().start()
        if args.ui_only:
            while True:
                time.sleep(1)
        if args.text:
            return run_terminal()
        from voice.voice_pipeline import LocalWakeVoicePipeline, list_microphones

        if args.list_microphones:
            devices = list_microphones()
            for device in devices:
                print(f"{device['index']} : {device['name']} ({device['sample_rate']} Hz)")
            if not devices:
                print("JARVIS > Aucun microphone disponible.")
            return 0
        print(f"JARVIS {VERSION} — Mode vocal : Jarvis + Kokoro", flush=True)
        if args.background:
            print(
                f"JARVIS > Session permanente : seuil {args.wake_threshold:.2f}, "
                f"suivi {args.followup_seconds:.0f}s sans nouveau réveil.",
                flush=True,
            )
            # Kokoro et le détecteur démarrent en parallèle : le micro n'attend
            # plus la fin du chargement TTS (~minutes sur ce GPU).
            from voice.voice_manager import prepare_voice_async
            prepare_voice_async()
        pipeline = LocalWakeVoicePipeline.from_defaults(
            sample_rate=args.sample_rate, threshold=args.wake_threshold,
        )
        pipeline.prepare_voice(announce=not args.background, background=args.background)
        failures = 0
        while True:
            try:
                pipeline.run_microphone(
                    device_index=args.mic_device, sample_rate=args.sample_rate,
                    command_seconds=args.command_seconds,
                    silence_seconds=args.silence_seconds, speech_threshold=args.speech_threshold,
                    endpointing=not args.raw_capture, followup_seconds=args.followup_seconds,
                    barge_in=not args.no_barge_in, keep_alive=args.background,
                )
                return 0
            except OSError:
                if not args.background:
                    raise
                failures += 1
                delay = min(60, 5 * failures)
                print(f"JARVIS > Micro indisponible, nouvelle tentative dans {delay} secondes.", flush=True)
                if failures >= MAX_BACKGROUND_MIC_FAILURES:
                    raise OSError(f"Microphone indisponible après {failures} tentatives")
                time.sleep(delay)
    except KeyboardInterrupt:
        print("\nJARVIS > Arrêt demandé. À bientôt, Fabrice.")
        return 0
    except ImportError as error:
        print(f"JARVIS > Dépendance indisponible : {error}. Lancez .venv-kokoro-cuda/bin/python main.py et vérifiez les dépendances de cet environnement.")
        return 1
    except Exception as error:
        print(f"JARVIS > Mode vocal indisponible : {error}. Vérifiez le microphone avec --list-microphones.")
        return 1
    finally:
        if ui_bridge:
            ui_bridge.stop()
        from core.capture.recording import screen_recorder
        screen_recorder.close()
        from core.vision.context import visual_session
        visual_session.clear()
        from core.vision.development import clear
        from core.vision.targets import select_target, VisualTarget
        from core.vision.providers import reset_session
        clear()
        select_target(VisualTarget())
        if runtime:
            runtime.stop()
        reset_session()
        app_lock.close()
        if old_signal is not None:
            signal.signal(signal.SIGTERM, old_signal)


if __name__ == "__main__":
    raise SystemExit(main())
