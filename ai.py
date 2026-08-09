from multiprocessing import get_context
from history import get_recent_history
from openai import OpenAI
import os
from dotenv import load_dotenv

from context import get_context
load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def ask_ai(message):
    history = get_recent_history(limit=10)
    try: 
        context = get_context()
        system_prompt = f"""Tu es JARVIS, l'assistant personnel de Fabrice.

Tu dois répondre naturellement, clairement et en français.

Voici les informations connues sur Fabrice :

{context}

Utilise ces informations uniquement lorsqu'elles sont pertinentes.
Ne prétends jamais connaître une information qui n'est pas présente
dans ton contexte.
"""
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        for conversation in history:
            messages.append({
                "role": "user",
                "content": conversation["user"]
            })
            messages.append({
                "role": "assistant",
                "content": conversation["jarvis"]
            })

        messages.append({
            "role": "user",
            "content": message
        })

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )

        

        return response.choices[0].message.content

    except Exception as e:
        print("Erreur Groq :", e)
        return "Désolé Fabrice, je rencontre un problème avec mon cerveau IA."