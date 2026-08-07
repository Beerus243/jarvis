from tools import open_browser, get_time, open_musique
import json
from personality import speak
from intent import detect_intent
from dispatcher import dispatch
from memory import save_history


def load_memory():
    with open("user.json", "r") as f:
        user = json.load(f)
        return user
user = load_memory()

def save_memory():
    with open("user.json", "w") as f:
        json.dump(user, f, indent=4)

def jarvis(message):
    message = message.lower()

    intent = detect_intent(message)
    response = dispatch(intent)
    if response:
        return response
    return "Je ne comprends pas."



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