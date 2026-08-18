import speech_recognition as sr

recognizer = sr.Recognizer()

recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.0
recognizer.non_speaking_duration = 0.5


def listen():

    with sr.Microphone() as source:

        print("🎤 J'écoute...")

        recognizer.adjust_for_ambient_noise(
            source,
            duration=1
        )

        try:
            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )

        except sr.WaitTimeoutError:
            print("JARVIS > Je n'ai rien entendu.")
            return None

    try:

        message = recognizer.recognize_google(
            audio,
            language="fr-FR"
        )

        print(f"Fabrice > {message}")

        return message.lower()

    except sr.UnknownValueError:

        print("JARVIS > Je n'ai pas compris.")
        return None

    except sr.RequestError as e:

        print("JARVIS > Erreur du service vocal :", e)
        return None