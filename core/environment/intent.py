from __future__ import annotations
from dataclasses import dataclass, field
import unicodedata
import re
from .profiles import DEFAULT_PROFILES

@dataclass(frozen=True)
class EnvironmentPreparationIntent:
    environment: str
    profile: str
    requested_version: str|None = None
    constraints: dict = field(default_factory=dict)
    confirmation_mode: str = 'ask'
    intent: str = 'ENVIRONMENT_REPAIR_PLAN'
    capability: str|None = None

def detect_environment_intent(message: str) -> EnvironmentPreparationIntent|None:
    text=(message or '').lower().strip()
    normalized = ' '.join(text.replace("'", " ").replace("’", " ").replace('-', ' ').split())
    normalized = ''.join(ch for ch in unicodedata.normalize('NFD', normalized) if not unicodedata.combining(ch))
    if normalized.startswith(('prepare ', 'prepare moi ', 'repare ', 'installe ')):
        if normalized in ('repare mon environnement', 'répare mon environnement'):
            return EnvironmentPreparationIntent('Environment', 'flutter_development', intent='ENVIRONMENT_REPAIR_PLAN')
        if 'android' in normalized:
            return EnvironmentPreparationIntent('Android', 'flutter_development', intent='ENVIRONMENT_REPAIR_PLAN')
        if 'ce qu il manque' in normalized:
            return EnvironmentPreparationIntent('Environment', 'flutter_development', intent='ENVIRONMENT_REPAIR_PLAN')
        if 'java' in normalized or 'jdk' in normalized:
            return EnvironmentPreparationIntent('Java', 'java', intent='JDK_INSTALL')
    confirmations = {"oui", "confirme", "je confirme", "vas y", "execute", "lance", "d accord", "ok"}
    cancellations = {"non", "annule", "annuler", "pas maintenant", "laisse tomber", "stop"}
    if normalized in confirmations:
        return EnvironmentPreparationIntent('Environment', 'flutter_development', intent='ENVIRONMENT_CONFIRM')
    if normalized in cancellations:
        return EnvironmentPreparationIntent('Environment', 'flutter_development', intent='ENVIRONMENT_CANCEL')
    checks = (
        ("ENVIRONMENT_GAPS", ("qu est ce qui manque", "qu'est ce qui manque", "qu est ce qui ne va pas", "liste les composants manquants", "pourquoi mon environnement n est pas pret"), None),
        ("FLUTTER_AUDIT", ("verifie flutter", "etat de flutter", "flutter est il pret", "mon flutter fonctionne"), "flutter"),
        ("ANDROID_AUDIT", ("verifie android", "analyse android", "etat android", "environnement android", "mon android est il pret"), "android"),
        ("JDK_AUDIT", ("verifie java", "verifie mon jdk", "verifie le jdk", "ai je un jdk", "mon jdk est il pret", "javac est il installe"), "jdk"),
        ("FLUTTER_ANDROID_BUILD_CHECK", ("compiler flutter android", "build android", "flutter android est pret"), "flutter_android_build"),
        ("ENVIRONMENT_AUDIT", ("verifie mon environnement", "analyse mon environnement", "fais un audit de mon environnement", "audit de mon environnement", "etat de mon environnement", "mon environnement est il pret", "est ce que mon environnement est pret"), "flutter_android_build"),
    )
    for intent, phrases, capability in checks:
        if any(phrase in normalized for phrase in phrases):
            return EnvironmentPreparationIntent("Environment", "flutter_development", intent=intent, capability=capability)
    for profile in DEFAULT_PROFILES.list():
        aliases=(profile.id,)+profile.aliases
        if any(re.search(r'(?<![\w])'+re.escape(alias.lower())+r'(?![\w])',text) for alias in aliases):
            version=(re.search(r'(?:version|v)\s*([0-9]+(?:\.[0-9]+)*)',text) or [None,None])[1]
            action = 'JDK_INSTALL' if profile.id == 'java' and any(w in normalized for w in ('installe', 'répare', 'repare')) else 'ENVIRONMENT_REPAIR_PLAN'
            if profile.id == 'flutter_development' and 'android' in normalized:
                action = 'ENVIRONMENT_REPAIR_PLAN'
            return EnvironmentPreparationIntent(profile.name,profile.id,version,intent=action)
    return None
