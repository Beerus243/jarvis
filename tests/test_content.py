from core.conversation import add_message
from core.context import get_context


add_message("user", "Ouvre Spotify")
add_message("assistant", "J'ouvre Spotify.")

add_message("user", "Mets ma musique préférée")
add_message("assistant", "Je vais lancer votre musique préférée.")


print("===== CONTEXTE =====")
print(get_context())
