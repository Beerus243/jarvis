"""Exécution des décisions produites par l'intelligence V3.0."""

from core import intelligence
from core.decision_context import build_decision_context
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
    decision_type = decision["type"]
    resolved_reference = context["reference"]
    reference_info = context.get("reference_info", {})

    if decision_type == "ACTION":
        return dispatch(decision["intent"])

    if decision_type == "PERSONAL_MEMORY":
        response = answer_personal_question(message)
        if response:
            return response

    if decision_type == "PROJECT_MEMORY":
        if decision["intent"] == "UPDATE":
            from memory.structured_memory import analyze_project_update

            return analyze_project_update(message)
        query = reference_info.get("query") or resolved_reference
        response = answer_project_question(query)
        if response:
            return response

    # CONTEXT et tous les cas locaux non résolus utilisent la référence existante.
    semantic_response = _semantic_fallback(message, resolved_reference)
    if semantic_response:
        return semantic_response

    return _ai_fallback(message, resolved_reference)
