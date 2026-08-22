"""Exécution d'un plan de réponse, sans nouvelle décision."""

from core.dispatcher import dispatch
from core.execution_result import ExecutionResult
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

    def success(response):
        if response is None:
            fallback = source in {"ACTION", "SEMANTIC_MEMORY", "AI"}
            return ExecutionResult(False, source or "UNKNOWN", error="Aucune réponse",
                                   fallback_allowed=fallback, error_type="NOT_FOUND")
        return ExecutionResult(True, source or "UNKNOWN", response=response, error_type="NONE")

    def failure(error, fallback_allowed=False, error_type="INTERNAL_ERROR"):
        return ExecutionResult(False, source or "UNKNOWN", error=str(error),
                               fallback_allowed=fallback_allowed, error_type=error_type)

    try:
        if source == "ACTION":
            return success(handlers.get("dispatch", dispatch)(response_plan.get("intent")))

        if source == "ACTION_COMPOSED":
            from core.action_executor import execute_plan
            results = execute_plan(response_plan.get("intent", []), dispatcher=handlers.get("raw_dispatch", dispatch))
            if not results:
                return failure("Aucune action reconnue", fallback_allowed=False, error_type="NOT_FOUND")
            if all(item.success for item in results):
                return success(f"{len(results)} action(s) exécutée(s) avec succès.")
            completed = sum(item.success for item in results)
            return ExecutionResult(
                False,
                source or "ACTION_COMPOSED",
                response=f"{completed} action(s) réussie(s), puis une action a échoué : {results[-1].message}",
                error="ACTION_FAILED",
                fallback_allowed=False,
                error_type="ACTION_FAILED",
            )

        if source == "PERSONAL_MEMORY":
            return success(handlers.get("personal", answer_personal_question)(message))

        if source == "PC_CONTEXT":
            from core.pc_context import answer_pc_question
            return success(handlers.get("pc", answer_pc_question)(message, (context or {}).get("pc_context")))

        if source == "TASK":
            return success(handlers.get("task", lambda msg, intent: None)(message, response_plan.get("intent")))

        if source == "PERSONAL_STATE":
            from memory.personal_state import answer_personal_state_question, update_personal_state

            handler = update_personal_state if response_plan.get("intent") == "UPDATE" else answer_personal_state_question
            return success(handlers.get("state", handler)(message))

        if source == "PROJECT_MEMORY":
            if response_plan.get("intent") == "UPDATE":
                from memory.structured_memory import analyze_project_update

                return success(analyze_project_update(message))
            return success(handlers.get("project", answer_project_question)(_project_query(message, context)))

        if source == "CONTEXT":
            query = _project_query(message, context)
            if query != message:
                return success(handlers.get("project", answer_project_question)(query))
            return failure("Contexte insuffisant", error_type="AMBIGUOUS")

        if source == "SEMANTIC_MEMORY":
            result = handlers.get("semantic", _semantic_search)(_project_query(message, context))
            return success(result.get("contenu", "") if result else None)

        if source == "AI":
            return success(handlers.get("ai", _ask_ai)(_project_query(message, context)))

        if source == "CLARIFICATION":
            return ExecutionResult(
                True,
                "CLARIFICATION",
                response="Je ne suis pas certain de ce que tu veux dire.",
            )

        return failure("Source inconnue", fallback_allowed=False, error_type="INTERNAL_ERROR")
    except Exception as error:
        if source == "SEMANTIC_MEMORY":
            return failure(error, fallback_allowed=False, error_type="DEPENDENCY_ERROR")
        if source == "AI":
            return failure(error, fallback_allowed=False, error_type="EXTERNAL_ERROR")
        return failure(error, fallback_allowed=False, error_type="INTERNAL_ERROR")
