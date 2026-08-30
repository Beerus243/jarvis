"""Conversation-facing adapter for the existing environment engine."""
from .capabilities import check_environment, format_capability_report, discover_capabilities

def handle_environment_intent(intent):
    capability = getattr(intent, "capability", None)
    if capability:
        return format_capability_report(check_environment(capability, capabilities=discover_capabilities()))
    if getattr(intent, "intent", "") == "ENVIRONMENT_GAPS":
        caps = discover_capabilities()
        result = check_environment("flutter_android_build", capabilities=caps)
        missing_items = list(result["missing"])
        for item in ("java_home", "sdkmanager"):
            if not getattr(caps, item) and item not in missing_items:
                missing_items.append(item)
        missing = ", ".join(missing_items) or "aucun composant"
        return f"Composants manquants : {missing}."
    if getattr(intent, "intent", "").endswith("INSTALL"):
        return "Une installation nécessite un artefact officiel validé et une confirmation explicite."
    return "Je peux préparer un plan de réparation contrôlé, sans rien installer automatiquement."
