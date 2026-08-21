"""Exécution d'un plan de réponse, sans nouvelle décision."""

from core.dispatcher import dispatch
from memory.personal_memory import answer_personal_question
from memory.structured_memory import answer_project_question


def _semantic_search(query):
    from memory import find_semantic_memory

    return find_semantic_memory(query, debug=False)


def _ask_ai(query):
    from ai.ai import ask_ai

    return ask_ai(query)


def _project_query(message, context):
    context = context or {}
    reference_info = context.get("reference_info", {})
    return reference_info.get("query") or context.get("reference") or message


def execute(response_plan, message, context=None, handlers=None):
    """Exécute exactement la source indiquée par le plan."""
    response_plan = response_plan or {}
    handlers = handlers or {}
    source = response_plan.get("source")

    if source == "ACTION":
        return handlers.get("dispatch", dispatch)(response_plan.get("intent"))

    if source == "PERSONAL_MEMORY":
        return handlers.get("personal", answer_personal_question)(message)

    if source == "PROJECT_MEMORY":
        if response_plan.get("intent") == "UPDATE":
            from memory.structured_memory import analyze_project_update

            return analyze_project_update(message)
        return handlers.get("project", answer_project_question)(_project_query(message, context))

    if source == "CONTEXT":
        query = _project_query(message, context)
        if query != message:
            return handlers.get("project", answer_project_question)(query)
        return None

    if source == "SEMANTIC_MEMORY":
        result = handlers.get("semantic", _semantic_search)(_project_query(message, context))
        return result.get("contenu", "") if result else None

    if source == "AI":
        return handlers.get("ai", _ask_ai)(_project_query(message, context))

    if source == "CLARIFICATION":
        return "Je ne suis pas certain de ce que tu veux dire. Peux-tu préciser ?"

    return None
