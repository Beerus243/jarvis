# ============================================================
# main.py - JARVIS version terminal
# Toutes les fonctions vocales sont commentées (conservées pour référence)
# Utilise la saisie clavier via input()
# ============================================================

# --- Imports principaux ---
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

# --- Imports vocaux (commentés) ---
# from listen import listen
# from voice import speak
# from wake_word import detect_wake_word
# from voice_loop import start_voice_loop
# from brain import think
# from memory_ai import analyze_memory

# Nettoyage des doublons (garder une seule fois chaque import)

# ============================================================
# 1. Gestion de la mémoire utilisateur
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
# 2. Fonction principale JARVIS
# ============================================================

def jarvis(message):
    """
    Traite un message texte et retourne une réponse.
    Version adaptée au terminal (sans appel vocal).
    """

    # 1. Détection d'intention
    intent = detect_intent(message)
    response = dispatch(intent)
    if response:
        return response

    # 2. Analyse de la mémoire (commenté car import absent)
    # memory_response = analyze_memory(message)
    # if memory_response:
    #     return memory_response

    # 3. Analyse du profil
    profile_response = analyze_profile(message)
    if profile_response:
        return profile_response

    # 4. Analyse des habitudes
    habit_response = analyze_habit(message)
    if habit_response:
        return habit_response

    # 5. Réponse par défaut (via le module voice ?)
    #    On utilise plutôt ask_ai en dernier recours
    # response = speak(message)  # commenté car speak est vocal
    # if response:
    #     return response

    # 6. Intelligence artificielle générale
    return ask_ai(message)

# ============================================================
# 3. Lancement en mode terminal (remplace start_voice_loop)
# ============================================================

if __name__ == "__main__":
    print("================================")
    print("          JARVIS V1.1")
    print("          Mode Terminal")
    print("================================")
    print("Bonjour Fabrice.")
    print("JARVIS est opérationnel.")
    print("Tapez vos commandes ci-dessous.")
    print("Tapez 'quitter' ou 'exit' pour arrêter.\n")

    while True:
        try:
            # Saisie utilisateur
            message = input("Fabrice > ").strip()

            # Commande de sortie
            if message.lower() in ["quitter", "exit", "stop", "au revoir"]:
                print("JARVIS > Au revoir Fabrice. J'arrête.")
                break

            # Traitement de la commande
            reponse = jarvis(message)
            print(f"JARVIS > {reponse}")

        except KeyboardInterrupt:
            print("\nJARVIS > Arrêt demandé. À bientôt.")
            break
        except Exception as e:
            print(f"JARVIS > Erreur : {e}")

# ============================================================
# Ancien lancement vocal (commenté)
# ============================================================
# print("Dites 'JARVIS' pour m'activer.")
# start_voice_loop()