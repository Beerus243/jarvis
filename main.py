from habits import analyze_habit
from history import save_message
from tools import open_browser, get_time, open_musique
import json
from personality import speak
from intent import detect_intent
from dispatcher import dispatch
from memory import save_history
from profile import analyze_profile
from ai import ask_ai
from listen import listen
from brain import think
from voice import speak
from memory_ai import analyze_memory
from brain import think
from history import save_message
from listen import listen
from listen import listen
from wake_word import detect_wake_word
from brain import think
from voice import speak


def load_memory():
    with open("user.json", "r") as f:
        user = json.load(f)
        return user
user = load_memory()

def save_memory():
    with open("user.json", "w") as f:
        json.dump(user, f, indent=4)

def jarvis(message):

    intent = detect_intent(message)

    response = dispatch(intent)

    if response:
        return response
    memory_response = analyze_memory(message)

    if memory_response:
        return memory_response

    profile_response = analyze_profile(message)

    memory_response = analyze_memory(message)

    if memory_response:
        return memory_response

    if profile_response:
        return profile_response

    habit_response = analyze_habit(message)

    if habit_response:
        return habit_response


    response = speak(message)

    if response:
        return response


    return ask_ai(message)



# Démarrage de JARVIS
print("================================")
print("          JARVIS V1.1")
print("================================")
print("Bonjour Fabrice.")
print("JARVIS est opérationnel.")
print("Dites 'JARVIS' pour m'activer.")


while True:

    message = listen()

    if not message:
        continue

    if message in ["quitter", "bye", "adieu", "arrête"]:

        speak("À bientôt Fabrice.")
        break

    if detect_wake_word(message):

        speak("Je vous écoute, Fabrice.")

        command = listen()

        if command:

            response = think(command)

            print("JARVIS >", response)

            speak(response)