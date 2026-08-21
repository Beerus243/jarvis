import os

from dotenv import load_dotenv
from openai import OpenAI

from core.context import get_context
from config.settings import MODEL as DEFAULT_MODEL


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = None


def _get_client():
    global client
    if client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY introuvable. Vérifie ton fichier .env.")
        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
    return client


# Modèle récent recommandé par Groq après le retrait de Llama 3.3.
MODEL = os.getenv("MODEL", DEFAULT_MODEL)


def ask_ai(message, memory_context=""):

    context = get_context()

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es JARVIS, l'assistant personnel de Fabrice. "
"Réponds toujours en français. "
"Adapte la longueur de ta réponse à la question. "
"Pour une question simple, réponds brièvement. "
"Pour une question nécessitant une explication, réponds "
"clairement et suffisamment en détail. "
"N'invente jamais une information absente de ta mémoire. "
"Lorsque la mémoire fournie contient une information fiable, "
"utilise-la comme source de vérité. "
"Ne prétends jamais qu'une conversation ou un événement a eu "
"lieu s'il n'est pas présent dans le contexte fourni."
                "Utilise l'historique fourni pour comprendre "
                "les références aux messages précédents. "
                "Si l'utilisateur dit 'il', 'elle', 'ça', 'ce projet', "
                "etc., utilise le contexte précédent pour déterminer "
                "ce à quoi il fait référence.\n\n"

            "Voici les souvenirs pertinents de Fabrice :\n"
            f"{memory_context}"
            )
        }
    ]


    # Ajouter l'historique

    messages.extend(context)


    # Ajouter le message actuel

    messages.append({
        "role": "user",
        "content": message
    })


    try:

        response = _get_client().chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )

        return response.choices[0].message.content


    except Exception as error:

        err_str = str(error)
        print(f"Erreur Groq : {err_str}")

        # Fournir un message clair si le modèle est introuvable
        if "model_not_found" in err_str or "does not exist" in err_str:
            return (
                "Désolé Fabrice, le modèle demandé n'est pas disponible "
                "ou tu n'y as pas accès. Vérifie la variable d'environnement "
                "`MODEL` dans ton fichier .env (par ex. "
                "MODEL=openai/gpt-oss-120b) "
                "ou demande l'accès au modèle auprès du fournisseur."
            )

        return (
            "Désolé Fabrice, je rencontre un problème avec mon cerveau IA."
        )
