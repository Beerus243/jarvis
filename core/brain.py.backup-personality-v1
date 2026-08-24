from core.conversation import add_message
from core.orchestrator import process

# Compatibilité avec les tests/intégrations qui remplaçaient cet ancien point
# d'injection. L'appel réel est désormais géré par l'orchestrateur.
ask_ai = None


def think(message):
    response = process(message)
    add_message("user", message)
    if response:
        add_message("assistant", response)
    return response
