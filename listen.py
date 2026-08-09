import speech_recognition as sr

recognizer = sr.Recognizer()


def listen():

    with sr.Microphone(device_index=14) as source:

        print("🎤 J'écoute...")

        recognizer.adjust_for_ambient_noise(source, duration=1)

        audio = recognizer.listen(source)

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