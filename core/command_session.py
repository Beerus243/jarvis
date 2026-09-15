"""Commandes de session partagées par le terminal et l'entrée vocale."""

import re
import unicodedata

EXIT_COMMANDS = {"quitter", "quit", "exit", "stop", "au revoir", "bye", "adieu", "arrete", "q"}
GOODBYE = "Au revoir Fabrice. À bientôt."


def is_exit_command(message):
    normalized = unicodedata.normalize("NFD", str(message).casefold())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = " ".join(re.sub(r"[^\w\s]", " ", normalized).split())
    if normalized not in EXIT_COMMANDS:
        return False
    if normalized in {"stop", "arrete"}:
        from core.environment.pending_plan import get_pending
        from core.task_engine import get_active_task
        from core.pending_action import get_pending as get_pending_action

        from core.runtime import get_runtime
        runtime = get_runtime()
        if runtime and runtime.personal_agent.pending():
            return False

        # Une annulation doit atteindre le cerveau lorsqu'un plan est actif.
        if get_pending() is not None or get_pending_action() is not None or get_active_task():
            return False
    return True


def process_command(message):
    """Point commun : toutes les commandes passent par le cerveau existant."""
    from core.brain import think

    return think(message)
