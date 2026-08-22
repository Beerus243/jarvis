# ============================================================
# main.py - JARVIS V3.2
# Mode terminal
# ============================================================

# ============================================================
# IMPORTS
# ============================================================

# Cerveau principal
from core.brain import think

# Mémoire utilisateur
import json
import sys
from config.settings import MEMORY_FILE

# Modules conservés pour l'architecture de JARVIS
from core.habits import analyze_habit
from core.history import save_message
from tools.tools import open_browser, get_time, open_musique
from personality.personality import speak
from core.intent import detect_intent
from core.dispatcher import dispatch
from voice.voice_manager import speak as speak_response


# ============================================================
# MÉMOIRE UTILISATEUR
# ============================================================

def load_memory():

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:

        user = json.load(f)

    return user


user = load_memory()


def save_memory():

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:

        json.dump(user, f, indent=4)


# ============================================================
# CONFIGURATION
# ============================================================

VERSION = "V4.4"
EXIT_COMMANDS = {
    "quitter",
    "quit",
    "exit",
    "stop",
    "au revoir",
    "bye",
    "adieu",
    "arrete",
    "q",
}


def is_exit_command(message):
    """Reconnaît une commande d'arrêt malgré casse, accents ou ponctuation."""

    import re
    import unicodedata

    normalized = unicodedata.normalize("NFD", message.casefold())
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = " ".join(normalized.split())
    return normalized in EXIT_COMMANDS


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
            if is_exit_command(message):

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
                speak_response(response)

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

    if "--voice" in sys.argv[1:]:
        from voice.assistant_loop import AssistantLoop

        print("JARVIS en veille...")
        AssistantLoop().run()
    else:
        main()
