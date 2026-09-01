"""Choix pur de la source de réponse, sans effet de bord."""


def plan(decision):
    """Transforme une décision d'intelligence en plan d'exécution."""
    decision = decision or {}
    decision_type = decision.get("type")
    confidence = float(decision.get("confidence", 0.0))
    ambiguous = bool(decision.get("ambiguous", False))

    if decision_type == "SELF_MODIFICATION_REFUSAL":
        return {"source": "SELF_MODIFICATION_REFUSAL", "intent": None, "confidence": confidence, "requires_memory": False, "requires_ai": False, "ambiguous": False}
    if decision_type in {"ACTION", "ACTION_COMPOSED", "USER_STATE", "PERSONAL_MEMORY", "PERSONAL_STATE", "PROJECT_MEMORY", "PC_CONTEXT", "TASK", "ENVIRONMENT"}:
        if ambiguous or confidence < 0.70:
            source = "SEMANTIC_MEMORY" if decision.get("requires_memory") else "AI"
        else:
            source = decision_type
    elif decision_type == "CONTEXT":
        source = "CLARIFICATION" if ambiguous or confidence < 0.50 else "CONTEXT"
    elif decision_type == "GENERAL_AI":
        source = "AI"
    elif decision_type == "CLARIFICATION":
        source = "CLARIFICATION"
    else:
        source = "CLARIFICATION" if ambiguous or confidence < 0.50 else "AI"

    return {
        "source": source,
        "intent": decision.get("intent"),
        "confidence": confidence,
        "requires_memory": source in {"USER_STATE", "PERSONAL_MEMORY", "PERSONAL_STATE", "PROJECT_MEMORY", "PC_CONTEXT", "TASK", "CONTEXT", "SEMANTIC_MEMORY"},
        "requires_ai": source == "AI",
        "ambiguous": ambiguous or source == "CLARIFICATION",
    }
