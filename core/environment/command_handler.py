"""Conversation-facing adapter for the existing environment engine."""
from .capabilities import check_environment, format_capability_report, discover_capabilities
from .pending_plan import set_pending, get_pending, clear_pending
from .installation_engine import InstallationEngine
from .lock import InstallationLock
from pathlib import Path

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
    if getattr(intent, "intent", "") == "ENVIRONMENT_CONFIRM":
        pending = get_pending()
        if not pending:
            return "Aucun plan d'environnement n'est en attente."
        if pending.plan is not None and pending.artifact is not None:
            artifact = pending.artifact
            source = getattr(artifact, "source", None)
            approved = source.approved() if source and hasattr(source, "approved") else bool(getattr(source, "trusted", False))
            if not approved or not getattr(artifact, "checksum", None):
                clear_pending(); return "PLAN_INVALIDATED : artefact non validé. Aucune modification n'a été effectuée."
            destination = Path(artifact.destination).expanduser().resolve()
            if Path.home().resolve() not in destination.parents:
                clear_pending(); return "PLAN_INVALIDATED : destination hors espace utilisateur."
            try:
                with InstallationLock():
                    report = InstallationEngine().execute(pending.plan, artifact=artifact, dry_run=False, confirmation_handler=lambda _step: True)
            except RuntimeError:
                return "INSTALLATION_LOCKED : une autre réparation est déjà en cours."
            clear_pending()
            return "Réparation terminée." if report.to_dict().get("success") else "Réparation échouée. Aucune réussite n'est déclarée."
        clear_pending()
        return "Le plan ne peut pas démarrer : aucun artefact officiel validé n'est actuellement disponible."
    if getattr(intent, "intent", "") == "ENVIRONMENT_CANCEL":
        if get_pending():
            clear_pending(); return "Plan d'environnement annulé."
        return "Aucun plan d'environnement n'est en attente."
    if getattr(intent, "intent", "").endswith("INSTALL"):
        set_pending(intent)
        return "Une installation nécessite un artefact officiel validé et une confirmation explicite."
    if getattr(intent, "intent", "") == "ENVIRONMENT_REPAIR_PLAN":
        pending = set_pending(intent)
        return f"Plan {pending.plan_id} préparé. Aucune modification n'a encore été effectuée. Confirmez-vous son exécution ?"
    return "Je peux préparer un plan de réparation contrôlé, sans rien installer automatiquement."
