import intent
from tools import open_browser, get_time, open_musique
import json
from personality import speak
from intent import detect_intent


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
    
    if intent == "GET_TIME":
        heure = get_time()
        return f"Il est actuellement {heure}"
    
    elif intent == "OPEN_BROWSER":
        return open_browser()
    
    elif intent == "PLAY_MUSIC":
        return open_musique()

    elif "quelle sont mes passions" in message:
        return f"Vous aimez {user['identite']['passion']}"

    elif "qui suis-je" in message:
        return f"vous êtes {user['identite']['name']} {user['identite']['postnom']}, vous habitez à {user['identite']['ville']} et vous êtes passionné par {user['identite']['passion']}."

    elif "qui es-tu" in message:
        return "Je suis JARVIS, votre assistant personnel."

    elif "c'est quoi ton nom" in message:
        return "Je suis JARVIS, un assistant créé par Fabrice pour vous aider."

    elif "retiens que ma musique préférée est" in message:
        musique = message.split()[-1]
        user['preferences']['musique'] = musique
        save_memory()
        return f"J'ai retenu que votre musique préférée est {musique}."

    elif "retiens que ma couleur préférée est" in message:
        couleur = message.split()[-1]
        user['preferences']['couleur'] = couleur
        save_memory()
        return f"J'ai retenu que votre couleur préférée est {couleur}."

    elif "quelle est ma couleur préférée" in message:
        return f"Votre couleur préférée est {user['preferences']['couleur']}."

    reponse = speak(message)

    if reponse:
        return reponse

    else:
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