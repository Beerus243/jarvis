from listen import listen
from wake_word import detect_wake_word
from voice import speak
from brain import think


def start_voice_loop():

    print("🎤 JARVIS attend une commande...")

    while True:

        message = listen()

        if not message:
            continue

        if message in ["quitter", "bye", "adieu", "arrête"]:
            speak("À bientôt Fabrice.")
            break

        if detect_wake_word(message):

            # On retire le mot "jarvis"
            command = message.replace("jarvis", "").strip()

            # Si aucune commande n'a été donnée
            if not command:

                speak("Je vous écoute, Fabrice.")
                command = listen()

                if not command:
                    continue

            response = think(command)

            print("JARVIS >", response)

            speak(response)