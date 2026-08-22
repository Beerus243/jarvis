"""Choix pur de la source de réponse, sans effet de bord."""


def plan(decision):
    """Transforme une décision d'intelligence en plan d'exécution."""
    decision = decision or {}
    decision_type = decision.get("type")
    confidence = float(decision.get("confidence", 0.0))
    ambiguous = bool(decision.get("ambiguous", False))

    if decision_type in {"ACTION", "PERSONAL_MEMORY", "PERSONAL_STATE", "PROJECT_MEMORY", "PC_CONTEXT"}:
        if ambiguous or confidence < 0.70:
            source = "SEMANTIC_MEMORY" if decision.get("requires_memory") else "AI"
        else:
            source = decision_type
    elif decision_type == "CONTEXT":
        source = "CLARIFICATION" if ambiguous or confidence < 0.50 else "CONTEXT"
    elif decision_type == "GENERAL_AI":
        source = "AI"
    else:
        source = "CLARIFICATION" if ambiguous or confidence < 0.50 else "AI"

    return {
        "source": source,
        "intent": decision.get("intent"),
        "confidence": confidence,
        "requires_memory": source in {"PERSONAL_MEMORY", "PERSONAL_STATE", "PROJECT_MEMORY", "PC_CONTEXT", "CONTEXT", "SEMANTIC_MEMORY"},
        "requires_ai": source == "AI",
        "ambiguous": ambiguous or source == "CLARIFICATION",
    }
