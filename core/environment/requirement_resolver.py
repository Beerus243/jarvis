"""Read-only matching of user requests against the inspected environment."""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from typing import Any, Callable

from .inspector import inspect_environment
from .requirements import Requirement, RequirementPlan, RequirementStatus
from .profiles import DEFAULT_PROFILES, EnvironmentProfile


def _text(value: Any) -> str:
    return value.value if isinstance(value, RequirementStatus) else str(value or "")


def _status(check: Mapping[str, Any] | None) -> str:
    return _text((check or {}).get("status", RequirementStatus.UNKNOWN.value)).upper()


def _normalise(value: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", value.lower())
                   if not unicodedata.combining(ch))


def _command_requirement(name: str, label: str, environment: Mapping[str, Any],
                         *, required: bool = True, depends_on: list[str] | None = None) -> Requirement:
    check = (environment.get("commands") or {}).get(name)
    state = _status(check)
    mapping = {"PRESENT": RequirementStatus.SATISFIED, "ABSENT": RequirementStatus.MISSING,
               "MISCONFIGURED": RequirementStatus.MISCONFIGURED,
               "UNKNOWN": RequirementStatus.UNKNOWN}
    status = mapping.get(state, RequirementStatus.UNKNOWN)
    return Requirement(name=name, description=label, status=status, required=required,
                       detected_value=(check or {}).get("path") or (check or {}).get("version"),
                       recommendation=f"Installer ou configurer {label}" if status != RequirementStatus.SATISFIED else None,
                       depends_on=depends_on or [], details=dict(check or {}))


def _android_requirements(environment: Mapping[str, Any]) -> tuple[Requirement, Requirement]:
    android = environment.get("android") or {}
    sdk = android.get("android_sdk") or {}
    sdk_state = _status(sdk)
    sdk_status = {"PRESENT": RequirementStatus.SATISFIED, "ABSENT": RequirementStatus.MISSING,
                  "MISCONFIGURED": RequirementStatus.MISCONFIGURED}.get(sdk_state, RequirementStatus.UNKNOWN)
    sdk_req = Requirement("android_sdk", "Android SDK", sdk_status, detected_value=sdk.get("path"),
                          recommendation="Installer ou configurer l'Android SDK" if sdk_status != RequirementStatus.SATISFIED else None)
    adb_check = (environment.get("commands") or {}).get("adb") or {}
    adb_state = _status(adb_check)
    if adb_state == "PRESENT":
        adb_status = RequirementStatus.SATISFIED
    elif adb_state == "UNKNOWN":
        adb_status = RequirementStatus.UNKNOWN
    elif sdk_state == "PRESENT" and sdk.get("adb"):
        adb_status = RequirementStatus.MISCONFIGURED
    elif sdk_state == "ABSENT":
        adb_status = RequirementStatus.MISSING
    else:
        adb_status = RequirementStatus.UNKNOWN
    adb_req = Requirement("adb", "Android Debug Bridge", adb_status, detected_value=adb_check.get("path") or sdk.get("adb"),
                          recommendation="Ajouter adb au PATH" if adb_status == RequirementStatus.MISCONFIGURED else None,
                          depends_on=["android_sdk"], details=dict(adb_check))
    return sdk_req, adb_req


def _flutter_profile(environment: Mapping[str, Any]) -> list[Requirement]:
    requirements = [
        _command_requirement("flutter", "Flutter SDK", environment),
        _command_requirement("dart", "Dart", environment, depends_on=["flutter"]),
        _command_requirement("java", "Java/JDK", environment),
    ]
    javac = _command_requirement("javac", "javac (JDK)", environment, depends_on=["java"])
    java_state = _status((environment.get("commands") or {}).get("java"))
    if javac.status == RequirementStatus.MISSING and java_state == "PRESENT":
        javac.status = RequirementStatus.MISCONFIGURED
        javac.recommendation = "Configurer le PATH/JAVA_HOME pour exposer javac"
        javac.details["reason"] = "Java est présent mais javac est absent du PATH"
    requirements.append(javac)
    sdk, adb = _android_requirements(environment)
    requirements.extend((sdk, adb))
    studio = ((environment.get("android") or {}).get("android_studio")
              or (environment.get("applications") or {}).get("android_studio") or {})
    studio_state = _status(studio)
    requirements.append(Requirement("android_studio", "Android Studio",
                                    {"PRESENT": RequirementStatus.SATISFIED, "ABSENT": RequirementStatus.MISSING}.get(studio_state, RequirementStatus.UNKNOWN),
                                    required=False, detected_value=studio.get("path"), details=dict(studio)))
    requirements.append(_command_requirement("git", "Git", environment))
    return requirements


PROFILES: dict[str, Callable[[Mapping[str, Any]], list[Requirement]]] = {
    "flutter_development": _flutter_profile,
}


def _profile_for(request: str | EnvironmentProfile) -> str | None:
    if isinstance(request, EnvironmentProfile): return request.id
    text = _normalise(request)
    profile = DEFAULT_PROFILES.resolve(text)
    if profile is None:
        profile = next((p for p in DEFAULT_PROFILES.list() if any(alias in text for alias in p.aliases)), None)
    return profile.id if profile else None

def _generic_profile(profile: str, environment: Mapping[str, Any]) -> list[Requirement]:
    def cmd(name, label, required=True): return _command_requirement(name, label, environment, required=required)
    if profile == 'java':
        java=cmd('java','Java runtime'); javac=cmd('javac','javac (JDK)', True)
        if java.status == RequirementStatus.MISSING and javac.status == RequirementStatus.SATISFIED: java.status=RequirementStatus.PARTIAL
        return [java,javac]
    if profile in {'node','nextjs'}:
        items=[cmd('node','Node.js'),cmd('npm','npm'),cmd('git','Git')]
        if profile == 'nextjs': items.append(Requirement('nextjs','Next.js tooling',RequirementStatus.MISSING,required=False,depends_on=['node','npm']))
        return items
    return _flutter_profile(environment)


def resolve_requirements(request: str, environment: Mapping[str, Any] | None = None) -> RequirementPlan:
    """Resolve a request without installing, changing, or executing any action."""
    request = request or ""
    profile = _profile_for(request)
    if profile is None:
        return RequirementPlan(request=request, profile=None,
                               message="Aucun profil technique reconnu pour cette demande.")
    snapshot = environment if environment is not None else inspect_environment()
    requirements = PROFILES.get(profile, lambda env: _generic_profile(profile, env))(snapshot)
    gaps = [item for item in requirements if item.status != RequirementStatus.SATISFIED and item.required]
    rank = {"javac": 10, "adb": 20, "flutter": 30, "dart": 40, "android_sdk": 50, "git": 60,
            "android_studio": 70}
    actions = []
    for item in sorted((r for r in requirements if r.status != RequirementStatus.SATISFIED),
                       key=lambda r: rank.get(r.name, 100)):
        verb = "CONFIGURE" if item.status == RequirementStatus.MISCONFIGURED else "VERIFY" if item.status == RequirementStatus.UNKNOWN else "INSTALL"
        actions.append({"requirement": item.name, "status": _text(item.status), "action": verb,
                        "description": item.recommendation or f"Vérifier {item.description}"})
    return RequirementPlan(request=request, profile=profile, requirements=requirements,
                           gaps=gaps, actions=actions,
                           message="Analyse en lecture seule : aucune action n'est exécutée.")


def format_requirement_plan(plan: RequirementPlan) -> str:
    lines = ["JARVIS ENVIRONMENT ANALYSIS", f"Objectif : {plan.request}"]
    if plan.profile:
        lines.append(f"Profil : {plan.profile}")
    if plan.message:
        lines.extend(["", plan.message])
    lines.extend(["", "Exigences :"])
    marks = {RequirementStatus.SATISFIED.value: "✓", RequirementStatus.MISSING.value: "✗",
             RequirementStatus.MISCONFIGURED.value: "⚠", RequirementStatus.UNKNOWN.value: "⚠"}
    for item in plan.requirements:
        status = _text(item.status).upper()
        suffix = " (recommandé)" if not item.required else ""
        lines.append(f"  {marks.get(status, '⚠')} {item.description or item.name} — {status}{suffix}")
    lines.append("\nÉcarts :")
    if not plan.gaps:
        lines.append("  Aucun composant obligatoire manquant.")
    else:
        lines.extend(f"  - {item.description or item.name} : {_text(item.status)}" for item in plan.gaps)
    if plan.actions:
        lines.append("\nPlan abstrait :")
        lines.extend(f"  {index}. {item['description']}" for index, item in enumerate(plan.actions, 1))
    return "\n".join(lines)
