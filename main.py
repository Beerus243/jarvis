"""Point d'entrée vocal de JARVIS ; clavier facultatif pour le diagnostic."""

import argparse
import math

from core.command_session import GOODBYE, is_exit_command, process_command as think
from voice.voice_manager import speak as speak_response

VERSION = "V6.9"


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
    parser = argparse.ArgumentParser(description="JARVIS : Hey Jarvis et Kokoro par défaut ; --text pour le clavier.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--voice", action="store_true", help="Mode vocal (déjà activé par défaut).")
    modes.add_argument("--text", action="store_true", help="Mode clavier explicite pour le diagnostic.")
    modes.add_argument("--list-microphones", action="store_true", help="Afficher les microphones disponibles.")
    parser.add_argument("--mic-device", type=_device_index, default=None, help="Index du microphone (par défaut : celui du système).")
    parser.add_argument("--sample-rate", type=_positive_int, default=44100, help="Fréquence de capture en Hz (44100 par défaut).")
    parser.add_argument("--wake-threshold", type=_positive_float, default=0.40, help="Seuil de détection entre 0 et 1 (0.40 par défaut).")
    parser.add_argument("--command-seconds", type=_positive_float, default=20.0, help="Durée maximale d'une commande, en secondes (20 par défaut).")
    parser.add_argument("--silence-seconds", type=_positive_float, default=1.5, help="Pause qui termine une phrase, en secondes (1,5 par défaut).")
    parser.add_argument("--speech-threshold", type=_positive_float, default=120.0, help="Seuil d'énergie de début de parole (120 par défaut).")
    parser.add_argument("--followup-seconds", type=_positive_float, default=8.0, help="Attente d'une réponse sans répéter Hey Jarvis (8 secondes).")
    parser.add_argument("--raw-capture", action="store_true", help="Capture fixe de diagnostic, sans détection de fin de phrase.")
    parser.add_argument("--no-barge-in", action="store_true", help="Désactiver l'interruption de la voix par Hey Jarvis.")
    parser.add_argument("--no-proactive", action="store_true", help="Désactiver la surveillance et les rappels pour cette session.")
    return parser


def main(argv=None):
    from core.vision.health import migrate
    parser = build_parser()
    args = parser.parse_args(argv)
    voice_mode = not args.text and not args.list_microphones
    if args.wake_threshold > 1:
        parser.error("--wake-threshold doit être compris entre 0 et 1.")
    from core.runtime import Runtime
    runtime = None
    try:
        migrate()
        if not args.no_proactive and not args.list_microphones:
            def notify(message):
                print(f"\nJARVIS > {message}", flush=True)
                return True
            runtime = Runtime(notify=None if voice_mode else notify).start()
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
        print(f"JARVIS {VERSION} — Mode vocal : Hey Jarvis + Kokoro", flush=True)
        pipeline = LocalWakeVoicePipeline.from_defaults(
            sample_rate=args.sample_rate, threshold=args.wake_threshold,
        )
        pipeline.prepare_voice()
        pipeline.run_microphone(
            device_index=args.mic_device, sample_rate=args.sample_rate,
            command_seconds=args.command_seconds,
            silence_seconds=args.silence_seconds, speech_threshold=args.speech_threshold,
            endpointing=not args.raw_capture, followup_seconds=args.followup_seconds,
            barge_in=not args.no_barge_in,
        )
        return 0
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


if __name__ == "__main__":
    raise SystemExit(main())
