from openai import OpenAI
from dotenv import load_dotenv
from memory import remember
import os
import json


load_dotenv()


client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def analyze_memory(message):

    prompt = f"""
Tu es le système de mémoire de JARVIS.

Analyse le message suivant et détermine s'il contient
une information personnelle importante concernant Fabrice.

Message :
"{message}"

Si une information importante est présente,
retourne UNIQUEMENT un JSON sous cette forme :

{{
    "remember": true,
    "key": "nom_de_l_information",
    "value": "valeur"
}}

Sinon retourne :

{{
    "remember": false
}}

Ne retourne aucun texte supplémentaire.
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",

            messages=[
                {
                    "role": "system",
                    "content": "Tu es un système d'extraction de mémoire."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )


        result = response.choices[0].message.content

        data = json.loads(result)


        if data.get("remember"):

            remember(
                data["key"],
                data["value"]
            )

            return (
                f"J'ai retenu que "
                f"{data['key']} est {data['value']}."
            )


    except Exception as e:

        print("Erreur mémoire :", e)


    return None