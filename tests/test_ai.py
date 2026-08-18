from core.conversation import add_message
from ai.ai import ask_ai


add_message("user", "Je suis en train de travailler sur mon projet JARVIS.")

add_message(
    "assistant",
    "Très bien Fabrice, je suis prêt à vous aider."
)


question = "De quel projet est-ce que je parle ?"

print("Fabrice >", question)

response = ask_ai(question)

print("JARVIS >", response)
