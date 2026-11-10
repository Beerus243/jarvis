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
            base_url="https://api.groq.com/openai/v1",
            timeout=20,
            max_retries=0,
        )
    return client


# Modèle récent recommandé par Groq après le retrait de Llama 3.3.
MODEL = os.getenv("MODEL", DEFAULT_MODEL)


def ask_ai(message, memory_context=""):

    context = get_context()

    from personality.dialogue import system_prompt, response_tokens, context_message
    messages = [{"role": "system", "content": system_prompt(message)}]
    if memory_context:
        messages.append({"role": "user", "content": context_message(memory_context)})

    # Ajouter l'historique

    messages.extend({"role": item["role"], "content": item["content"]}
                    for item in context if isinstance(item, dict)
                    and item.get("role") in {"user", "assistant"}
                    and isinstance(item.get("content"), str))


    # Ajouter le message actuel

    messages.append({
        "role": "user",
        "content": message
    })


    try:

        response = _get_client().chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.55,
            max_tokens=response_tokens(message)
        )

        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            return "Je n’ai pas reçu de réponse exploitable. Vous pouvez reformuler votre demande."
        if response.choices[0].finish_reason == 'length':
            # Do not silently present a cut sentence/code block as a complete answer.
            content = content.rstrip() + "\nLa réponse a atteint sa limite de longueur ; je peux poursuivre sur demande."
        return content.strip()


    except Exception as error:

        err_str = str(error)
        print(f"Erreur Groq : {type(error).__name__}")

        if "model_not_found" in err_str or "does not exist" in err_str:
            return "Le modèle de dialogue configuré est indisponible. Le réglage MODEL doit être vérifié."
        if "429" in err_str or "rate_limit" in err_str:
            return "Le service de dialogue a atteint sa limite de requêtes. Réessayez dans un moment ; les commandes locales restent disponibles."
        return "Je n’arrive pas à joindre le service de dialogue. Les commandes locales restent disponibles."
