"""Commandes de session partagées par le terminal et l'entrée vocale."""

import re
import unicodedata
import threading
import time
import uuid

command_lock = threading.RLock()

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


def process_command(message, *, request_id=None, origin=None, conversation_id=None):
    """Point commun : toutes les commandes passent par le cerveau existant."""
    from core.brain import think

    from core.ui_bridge import events
    current = events.request_context()
    request_id = request_id or current.get('requestId') or uuid.uuid4().hex
    origin = origin or current.get('origin') or 'system'
    conversation_id = conversation_id or current.get('conversationId') or 'default'
    started_at = time.monotonic()
    with events.request_scope(request_id, origin, conversation_id):
        if not current.get('requestId'):
            events.command(request_id, origin, message, 'received', conversation_id=conversation_id)
        events.command(request_id, origin, message, 'started', conversation_id=conversation_id)
        with command_lock:
            events.message('user', message)
            events.command(request_id, origin, message, 'thinking', conversation_id=conversation_id)
            events.state('thinking', 'Traitement par le Core Python')
            try:
                response = think(message)
                if response is not None:
                    events.message('jarvis', response)
                events.command(
                    request_id, origin, message, 'completed',
                    conversation_id=conversation_id,
                    result=response if response is not None else 'Aucune réponse',
                    duration_ms=(time.monotonic() - started_at) * 1000,
                )
                return response
            except Exception as error:
                events.activity(str(error), status='error')
                events.command(
                    request_id, origin, message, 'failed',
                    conversation_id=conversation_id, detail=str(error),
                    duration_ms=(time.monotonic() - started_at) * 1000,
                )
                raise
            finally:
                events.state('idle', 'JARVIS prêt')
