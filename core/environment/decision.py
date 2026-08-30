"""Decision and presentation helpers built on EnvironmentCapabilities."""
from dataclasses import dataclass
from .capabilities import EnvironmentCapabilities

@dataclass(frozen=True)
class EnvironmentDecision:
    status: str
    missing: tuple[str, ...]
    action: str
    reason: str

def decide(capabilities: EnvironmentCapabilities, *, network_available=False):
    missing=[]
    if not capabilities.javac: missing.append("javac, le compilateur Java")
    if not capabilities.java_home: missing.append("JAVA_HOME")
    if not capabilities.sdkmanager: missing.append("Android command-line tools")
    if not missing: return EnvironmentDecision("READY", (), "NONE", "Toutes les capacités sont disponibles.")
    return EnvironmentDecision("REPAIRABLE" if network_available else "BLOCKED", tuple(missing), "REPAIR" if network_available else "WAIT_NETWORK", "Sources officielles inaccessibles." if not network_available else "Réparation contrôlée possible.")

def format_decision(decision, *, capability="flutter_android_build"):
    if capability == "flutter_android_build":
        if decision.status == "READY": return "Oui. Ton environnement Flutter Android est prêt pour compiler."
        return f"Pas encore. Il manque {', '.join(decision.missing)}." + (" Les sources officielles nécessaires sont actuellement inaccessibles." if decision.status == "BLOCKED" else " Je peux préparer un plan de réparation.")
    return "L'environnement est prêt." if decision.status == "READY" else f"Composants manquants : {', '.join(decision.missing)}."
