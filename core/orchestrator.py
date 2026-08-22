"""Exécution des décisions produites par l'intelligence V3.0."""

from core import intelligence
from core.decision_context import build_decision_context
from core.response_planner import plan
from core.response_executor import execute
from core.diagnostics import create_diagnostic_event, record_diagnostic, clear_diagnostics
from core.dispatcher import dispatch
from core.reference import resolve_reference
from memory.personal_memory import answer_personal_question
from memory.personal_state import answer_personal_state_question, update_personal_state
from memory.personal_state import get_personal_context
from core.action_executor import execute_action
from memory.structured_memory import answer_project_question
from core.pc_context import answer_pc_question
from core.task_engine import create_task, cancel_task, get_active_task, execute_task


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
    clear_diagnostics()
    context = build_decision_context(message)
    context["personal_context"] = get_personal_context()
    decision = intelligence.analyze(message, context=context)
    record_diagnostic(create_diagnostic_event(
        "INTELLIGENCE",
        source=decision.get("type"),
        confidence=decision.get("confidence"),
        message=message,
        metadata=decision,
    ))
    response_plan = plan(decision)
    # Une question complète « pourquoi/comment ... » reste une question IA,
    # même si un ancien échange est disponible dans l'historique.
    normalized_message = str(message or "").strip().lower()
    if response_plan.get("source") == "CONTEXT" and (
        normalized_message.startswith("pourquoi ")
        or normalized_message.startswith("comment ")
    ):
        response_plan = {**response_plan, "source": "AI", "requires_ai": True,
                         "requires_memory": False}
    record_diagnostic(create_diagnostic_event(
        "PLANNER",
        source=response_plan.get("source"),
        confidence=response_plan.get("confidence"),
        metadata=response_plan,
    ))
    result = execute(
        response_plan,
        message,
        context,
        handlers={
            "dispatch": lambda intent: execute_action(intent, dispatcher=dispatch).message,
            "personal": answer_personal_question,
            "state": lambda message: (
                update_personal_state(message)
                if response_plan.get("intent") == "UPDATE"
                else answer_personal_state_question(message)
            ),
            "project": answer_project_question,
            "pc": answer_pc_question,
            "task": lambda msg, intent: _handle_task(msg, intent),
            "semantic": lambda query: _semantic_fallback(message, query),
            "ai": lambda query: _ai_fallback(message, query),
        },
    )
    record_diagnostic(create_diagnostic_event(
        "EXECUTOR",
        source=result.source,
        success=result.success,
        message=result.error,
        metadata={
            "fallback_allowed": result.fallback_allowed,
            "error_type": result.error_type,
        },
    ))
    if result.success:
        return result.response

    if not result.fallback_allowed:
        if result.error_type == "AMBIGUOUS":
            return "Je ne suis pas certain de ce que tu veux dire."
        return None

    if result.source == "SEMANTIC_MEMORY":
        return _ai_fallback(message, context["reference"])

    # Une source locale absente autorise uniquement le fallback contrôlé.
    resolved_reference = context["reference"]
    semantic_response = _semantic_fallback(message, resolved_reference)
    if semantic_response:
        return semantic_response
    return _ai_fallback(message, resolved_reference)


def _handle_task(message, intent):
    if intent == "CANCEL":
        return "Tâche annulée." if cancel_task() else "Aucune tâche active."
    task = create_task(message)
    if not task.steps:
        return "Je n'ai pas pu construire une tâche sûre."
    result = execute_task(task, dispatcher=dispatch)
    if isinstance(result, tuple):
        task, results = result
        if task.status == "COMPLETED":
            return f"Tâche terminée : {len(results)} étape(s) exécutée(s)."
        return f"Tâche interrompue à l'étape {task.current_step}."
    return "Tâche planifiée."
