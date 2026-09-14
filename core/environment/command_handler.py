"""Conversation-facing adapter for the existing environment engine."""
from .capabilities import check_environment, format_capability_report, discover_capabilities
from .pending_plan import set_pending, get_pending, clear_pending
from .installation_engine import InstallationEngine
from .lock import InstallationLock
from pathlib import Path
from .decision import decide, format_decision

def handle_environment_intent(intent):
    capability = getattr(intent, "capability", None)
    if capability:
        caps = discover_capabilities()
        if capability == "flutter_android_build":
            return format_decision(decide(caps), capability=capability)
        return format_capability_report(check_environment(capability, capabilities=caps))
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
            from .conversation_plan import validate_plan_artifact
            if not validate_plan_artifact(artifact):
                clear_pending(); return "PLAN_INVALIDATED : métadonnées ou empreinte invalides."
            destination = Path(artifact.destination).expanduser().resolve()
            if Path.home().resolve() not in destination.parents:
                clear_pending(); return "PLAN_INVALIDATED : destination hors espace utilisateur."
            try:
                # Consommer avant toute action : un deuxième « oui » ne rejoue pas le plan.
                clear_pending()
                with InstallationLock():
                    report = InstallationEngine().execute(pending.plan, artifact=artifact, dry_run=False, confirmation_handler=lambda _step: True)
            except RuntimeError:
                return "INSTALLATION_LOCKED : une autre réparation est déjà en cours."
            clear_pending()
            if report.to_dict().get('success'):
                return f'Composant installé dans {destination}. Relance le terminal pour les variables d’environnement, puis demande « vérifie mon environnement ».'
            failed = next((r for r in report.results if r.error), None)
            return 'Installation échouée : ' + (failed.error if failed else 'résultat non vérifié')
        clear_pending()
        return "Le plan ne peut pas démarrer : aucun artefact officiel validé n'est actuellement disponible."
    if getattr(intent, "intent", "") == "ENVIRONMENT_CANCEL":
        if get_pending():
            clear_pending(); return "Plan d'environnement annulé."
        return "Aucun plan d'environnement n'est en attente."
    if getattr(intent, "intent", "").endswith("INSTALL") or intent.intent == "ENVIRONMENT_REPAIR_PLAN":
        from .conversation_plan import build_plan, validate_plan_artifact, format_plan
        try:
            if intent.environment == 'Environment':
                from dataclasses import replace
                caps = discover_capabilities()
                if not caps.flutter or not caps.dart:
                    intent = replace(intent, environment='Flutter')
                elif not caps.javac or not caps.java_runtime:
                    intent = replace(intent, environment='Java', profile='java', intent='JDK_INSTALL')
                elif not caps.sdkmanager:
                    intent = replace(intent, environment='Android', intent='ANDROID_TOOLS_INSTALL')
                else:
                    return format_decision(decide(caps)) + ' Les composants Android restants et les licences se gèrent dans le gestionnaire SDK.'
            plan, artifact = build_plan(intent)
            if not validate_plan_artifact(artifact):
                raise ValueError('Métadonnées officielles incomplètes ou empreinte invalide.')
            pending = set_pending(intent, plan=plan, artifact=artifact)
            return format_plan(pending)
        except Exception as error:
            pending = set_pending(intent)
            return f"Plan {pending.plan_id} bloqué : aucun artefact officiel validé. {error}"
    return "Je peux préparer un plan de réparation contrôlé, sans rien installer automatiquement."
