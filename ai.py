import os

from dotenv import load_dotenv
from openai import OpenAI

from context import get_context


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")


if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY introuvable. Vérifie ton fichier .env."
    )


client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


MODEL = "llama-3.3-70b-versatile"


def ask_ai(message, memory_context=""):

    context = get_context()

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es JARVIS, l'assistant personnel de Fabrice. "
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

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )

        return response.choices[0].message.content


    except Exception as error:

        print(f"Erreur Groq : {error}")

        return (
            "Désolé Fabrice, je rencontre "
            "un problème avec mon cerveau IA."
        )