# ============================================================
# main.py - JARVIS V1.1
# Mode terminal
# ============================================================

# ============================================================
# IMPORTS
# ============================================================

# Cerveau principal
from brain import think

# Mémoire utilisateur
import json

# Modules conservés pour l'architecture de JARVIS
from habits import analyze_habit
from history import save_message
from tools import open_browser, get_time, open_musique
from personality import speak
from intent import detect_intent
from dispatcher import dispatch
from profile import analyze_profile
from ai import ask_ai


# ============================================================
# MÉMOIRE UTILISATEUR
# ============================================================

def load_memory():

    with open("user.json", "r") as f:

        user = json.load(f)

    return user


user = load_memory()


def save_memory():

    with open("user.json", "w") as f:

        json.dump(user, f, indent=4)


# ============================================================
# CONFIGURATION
# ============================================================

VERSION = "V1.1"


# ============================================================
# AFFICHAGE
# ============================================================

def show_banner():

    print("================================")
    print(f"          JARVIS {VERSION}")
    print("          Mode Terminal")
    print("================================")
    print("Bonjour Fabrice.")
    print("JARVIS est opérationnel.")
    print("Tapez 'quitter' pour arrêter.")
    print()


# ============================================================
# BOUCLE PRINCIPALE
# ============================================================

def main():

    show_banner()

    while True:

        try:

            message = input("Fabrice > ").strip()

            # Ignorer une entrée vide
            if not message:
                continue

            # Commandes d'arrêt
            if message.lower() in [
                "quitter",
                "exit",
                "stop",
                "au revoir",
                "bye",
                "adieu"
            ]:

                print("JARVIS > Au revoir Fabrice. À bientôt.")
                break

            # ------------------------------------------------
            # ENVOI AU CERVEAU
            # ------------------------------------------------

            response = think(message)

            # ------------------------------------------------
            # AFFICHAGE DE LA RÉPONSE
            # ------------------------------------------------

            if response:

                print(f"JARVIS > {response}")

            else:

                print("JARVIS > Je n'ai pas de réponse.")

        except KeyboardInterrupt:

            print("\nJARVIS > Arrêt demandé. À bientôt, Fabrice.")
            break

        except Exception as error:

            print(f"JARVIS > Une erreur est survenue : {error}")


# ============================================================
# POINT D'ENTRÉE
# ============================================================

if __name__ == "__main__":

    main()
