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

import os

from groq import Groq

from context import get_context


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def ask_ai(message):

    context = get_context()

    system_prompt = """
Tu es JARVIS, un assistant personnel créé pour Fabrice.

Tu réponds en français.
Tu es poli, naturel, précis et concis.

Tu peux utiliser le contexte de conversation pour comprendre
les références comme "ça", "il", "elle", "le", "la", "cette chose",
etc.

Si le contexte ne permet pas de déterminer ce que Fabrice veut dire,
demande une précision au lieu d'inventer.
"""

    user_message = f"""
Contexte récent :

{context}

Nouvelle demande de Fabrice :

{message}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        temperature=0.7,
        max_tokens=500
    )

    return response.choices[0].message.content
