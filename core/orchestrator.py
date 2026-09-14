"""Exécution des décisions produites par l'intelligence V3.0."""

from core import intelligence
from core.decision_context import build_decision_context
from core.response_planner import plan
from core.response_executor import execute
from core.execution_result import CommandResponse
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
from personality.personality import personalize, clear_pending, remember_music_artist
from core.user_state import detect_user_state
from core.environment.preparation import EnvironmentPreparationEngine
from core.environment.action_planner import format_execution_plan
from core.environment.command_handler import handle_environment_intent
from personality.engine import AdvancedPersonalityEngine

# Instance unique du moteur avancé : il enrichit les réponses locales sans
# remplacer le moteur historique ni le dispatcher.
_advanced_personality = AdvancedPersonalityEngine()


def _semantic_fallback(message, resolved_reference):
    from memory import find_semantic_memory

    result = find_semantic_memory(resolved_reference, debug=False)
    if result:
        return result.get("contenu", "")
    return None


def _ai_fallback(message, resolved_reference, memory_context=""):
    from ai.ai import ask_ai
    from memory.service import relevant_context

    return ask_ai(resolved_reference, memory_context or relevant_context(message))


def process(message):
    clear_diagnostics()
    from core.session_service import handle_message
    session_response = handle_message(message, dispatcher=dispatch)
    if session_response is not None:
        if hasattr(session_response, "success"):
            record_diagnostic(create_diagnostic_event("EXECUTOR", source="ACTION", success=session_response.success,
                message=session_response.message, metadata={"error": session_response.error}))
            return CommandResponse(session_response.message)
        return CommandResponse(session_response)
    context = build_decision_context(message)
    context["personal_context"] = get_personal_context()
    context["user_state"] = detect_user_state(message)
    _advanced_personality.analyze_context(message, context.get("pc_context"), context.get("personal_context"))
    cultural = _advanced_personality.handle_cultural_reference(message)
    banter = _advanced_personality.handle_banter(message)
    decision = intelligence.analyze(message, context=context)
    if decision.get("type") in {"GENERAL_AI", "UNKNOWN"} and (cultural or banter):
        return cultural or banter
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
            "dispatch": _dispatch_action,
            "raw_dispatch": dispatch,
            "user_state": lambda msg, state: personalize(
                msg,
                None,
                {**context, "user_state": state},
            ),
            "personal": answer_personal_question,
            "state": lambda message: (
                update_personal_state(message)
                if response_plan.get("intent") == "UPDATE"
                else answer_personal_state_question(message)
            ),
            "project": answer_project_question,
            "pc": answer_pc_question,
            "task": lambda msg, intent: _handle_task(msg, intent),
            "composed": _handle_composed,
            "environment": lambda intent: handle_environment_intent(intent),
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
        return CommandResponse(result.response) if result.source in {'ACTION', 'ACTION_COMPOSED', 'TASK', 'ENVIRONMENT'} else result.response

    if not result.fallback_allowed:
        if result.error_type in {"ACTION_FAILED", "CONFIRMATION_REQUIRED"} and result.response:
            return CommandResponse(result.response)
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


def _handle_composed(message, actions):
    from core.runtime import get_runtime
    from core.execution_result import ExecutionResult
    task = create_task(message, steps=actions)
    runtime = get_runtime()
    if runtime:
        runtime.submit(task.id)
        return f'Tâche {task.id[:8]} démarrée : {len(task.steps)} étapes. Dis « annule la tâche » pour arrêter.'
    task, results = execute_task(task, dispatcher=dispatch)
    if task.status == 'COMPLETED':
        return f'{task.current_step} action(s) exécutée(s) avec succès.'
    waiting = task.status == 'WAITING_CONFIRMATION'
    return ExecutionResult(False, 'ACTION_COMPOSED',
        response=f'{task.current_step} action(s) réussie(s). {task.error or task.status}',
        error=task.error, error_type='CONFIRMATION_REQUIRED' if waiting else 'ACTION_FAILED')


def _handle_task(message, intent):
    if intent == "CANCEL":
        return "Tâche annulée." if cancel_task() else "Aucune tâche active."
    task = create_task(message)
    if not task.steps:
        return "Je n'ai pas pu construire une tâche sûre."
    from core.runtime import get_runtime
    runtime = get_runtime()
    if runtime:
        runtime.submit(task.id)
        return f"Tâche {task.id[:8]} démarrée : {len(task.steps)} étapes. Tu peux dire « annule la tâche »."
    result = execute_task(task, dispatcher=dispatch)
    if isinstance(result, tuple):
        task, results = result
        if task.status == "COMPLETED":
            return f"Tâche terminée : {len(results)} étape(s) exécutée(s)."
        return f"Tâche {task.status} à l'étape {task.current_step}. {task.error or ''}"
    return "Tâche planifiée."


def _dispatch_action(intent):
    result = execute_action(intent, dispatcher=dispatch)
    if not result.success and result.policy == "CONFIRMATION_REQUIRED":
        from core.pending_action import set_pending
        pending = set_pending(intent)
        result.message = f"Confirmer l'action {pending['id']} : {intent} ? Dites « confirme » ou « annule »."
    if result.success and isinstance(intent, dict) and intent.get("action") == "PLAY_MUSIC":
        remember_music_artist(intent.get("artist"))
        clear_pending()
    return result
