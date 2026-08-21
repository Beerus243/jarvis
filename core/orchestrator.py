"""Exécution des décisions produites par l'intelligence V3.0."""

from core import intelligence
from core.decision_context import build_decision_context
from core.response_planner import plan
from core.response_executor import execute
from core.dispatcher import dispatch
from core.reference import resolve_reference
from memory.personal_memory import answer_personal_question
from memory.structured_memory import answer_project_question


def _semantic_fallback(message, resolved_reference):
    from memory import find_semantic_memory

    result = find_semantic_memory(resolved_reference, debug=False)
    if result:
        return result.get("contenu", "")
    return None


def _ai_fallback(message, resolved_reference, memory_context=""):
    from ai.ai import ask_ai

    return ask_ai(resolved_reference, memory_context)


def process(message):
    context = build_decision_context(message)
    decision = intelligence.analyze(message, context=context)
    response_plan = plan(decision)
    result = execute(
        response_plan,
        message,
        context,
        handlers={
            "dispatch": dispatch,
            "personal": answer_personal_question,
            "project": answer_project_question,
            "semantic": lambda query: _semantic_fallback(message, query),
            "ai": lambda query: _ai_fallback(message, query),
        },
    )
    if result.success:
        return result.response

    if not result.fallback_allowed:
        return None

    # Une source locale absente autorise uniquement le fallback contrôlé.
    resolved_reference = context["reference"]
    semantic_response = _semantic_fallback(message, resolved_reference)
    if semantic_response:
        return semantic_response
    return _ai_fallback(message, resolved_reference)
