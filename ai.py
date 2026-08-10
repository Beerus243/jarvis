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


def ask_ai(message):

    context = get_context()

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es JARVIS, l'assistant personnel de Fabrice. "
                "Réponds toujours en français. "
                "Utilise l'historique fourni pour comprendre "
                "les références aux messages précédents. "
                "Si l'utilisateur dit 'il', 'elle', 'ça', 'ce projet', "
                "etc., utilise le contexte précédent pour déterminer "
                "ce à quoi il fait référence."
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
            max_tokens=100
        )

        return response.choices[0].message.content


    except Exception as error:

        print(f"Erreur Groq : {error}")

        return (
            "Désolé Fabrice, je rencontre "
            "un problème avec mon cerveau IA."
        )