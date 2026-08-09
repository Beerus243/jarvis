from habits import analyze_habit
from tools import open_browser, get_time, open_musique
import json
from personality import speak
from intent import detect_intent
from dispatcher import dispatch
from memory import save_history
from profile import analyze_profile
from ai import ask_ai


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


    profile_response = analyze_profile(message)

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
print("          JARVIS V0.5")
print("================================")
print("Bonjour Fabrice.")
print("JARVIS est opérationnel.")
print("Tapez 'quitter' pour arrêter.")


while True:

    message = input("\nFabrice > ")

    if message.lower() == "quitter":
        print("\nJARVIS > À bientôt, Fabrice.")
        break

    reponse = jarvis(message)

    print("JARVIS >", reponse)
    save_history(message, reponse)