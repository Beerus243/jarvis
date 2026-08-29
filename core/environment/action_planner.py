"""Build deterministic, read-only execution plans from requirement plans."""

from __future__ import annotations

from collections.abc import Callable

from .actions import ActionType, ExecutionPlan, PlannedAction, RiskLevel
from .requirement_resolver import resolve_requirements
from .requirements import Requirement, RequirementPlan, RequirementStatus


def _status(value: object) -> str:
    return getattr(value, "value", str(value)).upper()


class ActionProvider:
    """Strategy interface for mapping one requirement to abstract actions."""

    def supports(self, requirement: Requirement) -> bool:
        return False

    def actions_for(self, requirement: Requirement, ids: dict[str, str]) -> list[PlannedAction]:
        return []


class JavaActionProvider(ActionProvider):
    def supports(self, requirement: Requirement) -> bool:
        return requirement.name == "javac"

    def actions_for(self, requirement: Requirement, ids: dict[str, str]) -> list[PlannedAction]:
        if _status(requirement.status) != RequirementStatus.MISCONFIGURED.value:
            return []
        configure = PlannedAction("", "javac", ActionType.CONFIGURE,
                                 "Configurer javac dans le PATH/JAVA_HOME",
                                 reason="JDK détecté mais javac n'est pas disponible dans le PATH.",
                                 risk_level=RiskLevel.MEDIUM, requires_confirmation=True,
                                 verification="javac doit être détectable")
        verify = PlannedAction("", "javac", ActionType.VERIFY, "Vérifier javac",
                              dependencies=["__CONFIGURE__"], verification="javac --version")
        return [configure, verify]


class AndroidActionProvider(ActionProvider):
    def supports(self, requirement: Requirement) -> bool:
        return requirement.name == "adb"

    def actions_for(self, requirement: Requirement, ids: dict[str, str]) -> list[PlannedAction]:
        if _status(requirement.status) != RequirementStatus.MISCONFIGURED.value:
            return []
        configure = PlannedAction("", "adb", ActionType.CONFIGURE,
                                 "Ajouter adb au PATH", reason="Android SDK présent mais adb absent du PATH.",
                                 risk_level=RiskLevel.MEDIUM, requires_confirmation=True,
                                 verification="adb doit être détectable")
        verify = PlannedAction("", "adb", ActionType.VERIFY, "Vérifier adb",
                              dependencies=["__CONFIGURE__"], verification="adb version")
        return [configure, verify]


class FlutterActionProvider(ActionProvider):
    def supports(self, requirement: Requirement) -> bool:
        return requirement.name in {"flutter", "dart", "android_sdk"}

    def actions_for(self, requirement: Requirement, ids: dict[str, str]) -> list[PlannedAction]:
        state = _status(requirement.status)
        if state == RequirementStatus.MISSING.value and requirement.name == "flutter":
            install = PlannedAction("", "flutter", ActionType.INSTALL, "Installer ou configurer Flutter SDK",
                                    reason="Flutter SDK absent.", risk_level=RiskLevel.MEDIUM,
                                    reversible=True, requires_confirmation=True,
                                    verification="flutter --version")
            verify = PlannedAction("", "flutter", ActionType.VERIFY, "Vérifier Flutter",
                                  dependencies=["__INSTALL__"], verification="flutter doctor")
            return [install, verify]
        if requirement.name == "dart" and state in {"MISSING", "UNKNOWN"}:
            return [PlannedAction("", "dart", ActionType.VERIFY, "Vérifier Dart fourni par Flutter",
                                  reason="Dart est fourni par le SDK Flutter dans ce profil.",
                                  dependencies=[ids.get("flutter_verify", "")], verification="dart --version")]
        if requirement.name == "android_sdk" and state == RequirementStatus.MISSING.value:
            install = PlannedAction("", "android_sdk", ActionType.INSTALL, "Installer ou configurer Android SDK",
                                    reason="Android SDK absent.", risk_level=RiskLevel.MEDIUM,
                                    requires_confirmation=True, verification="SDK détectable")
            return [install]
        return []


class GenericActionProvider(ActionProvider):
    def supports(self, requirement: Requirement) -> bool:
        return True

    def actions_for(self, requirement: Requirement, ids: dict[str, str]) -> list[PlannedAction]:
        state = _status(requirement.status)
        if state == RequirementStatus.SATISFIED.value:
            return []
        if state == RequirementStatus.UNKNOWN.value:
            return [PlannedAction("", requirement.name, ActionType.MANUAL,
                                  f"Déterminer manuellement {requirement.description or requirement.name}",
                                  reason="L'inspection ne permet pas de déterminer une action sûre.",
                                  risk_level=RiskLevel.BLOCKED, reversible=False,
                                  requires_confirmation=True)]
        if not requirement.required:
            return [PlannedAction("", requirement.name, ActionType.SKIP,
                                  f"Ne pas installer {requirement.description or requirement.name}",
                                  reason="Composant recommandé mais non obligatoire.")]
        return [PlannedAction("", requirement.name, ActionType.INSTALL,
                              f"Installer ou configurer {requirement.description or requirement.name}",
                              reason=requirement.recommendation or "Composant absent.",
                              risk_level=RiskLevel.MEDIUM, requires_confirmation=True)]


PROVIDERS: tuple[ActionProvider, ...] = (JavaActionProvider(), AndroidActionProvider(),
                                         FlutterActionProvider(), GenericActionProvider())


def _topological(actions: list[PlannedAction]) -> list[PlannedAction]:
    by_id = {action.id: action for action in actions}
    result: list[PlannedAction] = []
    remaining = list(actions)
    rank = {"javac": 10, "adb": 20, "flutter": 30, "dart": 40,
            "android_sdk": 50, "android_toolchain": 60, "git": 70}
    while remaining:
        candidates = [a for a in remaining if all(dep in {x.id for x in result} for dep in a.dependencies)]
        ready = min(candidates, key=lambda a: (rank.get(a.requirement, 100), a.id)) if candidates else None
        if ready is None:  # malformed external dependency: preserve deterministic order
            result.extend(remaining)
            break
        result.append(ready)
        remaining.remove(ready)
    return result


def plan_actions(requirement_plan: RequirementPlan) -> ExecutionPlan:
    actions: list[PlannedAction] = []
    ids: dict[str, str] = {}
    for requirement in requirement_plan.requirements:
        provider = next(item for item in PROVIDERS if item.supports(requirement))
        generated = provider.actions_for(requirement, ids)
        actions.extend(generated)
    # Assign IDs once, then resolve symbolic dependencies to those IDs.
    for index, action in enumerate(actions, 1):
        action.id = f"A{index:03d}"
    for requirement_name in {a.requirement for a in actions}:
        group = [a for a in actions if a.requirement == requirement_name]
        configure = next((a.id for a in group if a.action_type in (ActionType.CONFIGURE, ActionType.INSTALL)), None)
        for action in group:
            action.dependencies = [configure if dep.startswith("__") and configure else dep
                                   for dep in action.dependencies if dep and dep != "__PENDING_FLUTTER_VERIFY__"]
    flutter_verify = next((a.id for a in actions if a.requirement == "flutter" and a.action_type == ActionType.VERIFY), None)
    for action in actions:
        if action.requirement == "dart" and flutter_verify:
            action.dependencies = [flutter_verify]
    # Add the aggregate toolchain check only for a Flutter profile with unresolved work.
    if requirement_plan.profile == "flutter_development" and any(a for a in actions):
        deps = [a.id for a in actions if a.requirement in {"javac", "adb", "flutter"} and a.action_type == ActionType.VERIFY]
        actions.append(PlannedAction(f"A{len(actions)+1:03d}", "android_toolchain", ActionType.VERIFY,
                                    "Vérifier Android toolchain", dependencies=deps,
                                    verification="flutter doctor --android-licenses"))
    ordered = _topological(actions)
    return ExecutionPlan(profile=requirement_plan.profile, objective=requirement_plan.request,
                         actions=ordered, warnings=([] if not requirement_plan.message else [requirement_plan.message]))


def plan_environment_setup(request: str, environment: dict | None = None) -> ExecutionPlan:
    return plan_actions(resolve_requirements(request, environment=environment))


def format_execution_plan(plan: ExecutionPlan) -> str:
    lines = ["JARVIS ACTION PLAN", "", "OBJECTIVE", plan.objective, "", "ACTIONS"]
    for index, action in enumerate(plan.actions, 1):
        deps = " ".join(action.dependencies) or "aucune"
        confirm = "YES" if action.requires_confirmation else "NO"
        lines.extend([f"\n[{index}] {getattr(action.action_type, 'value', action.action_type)}",
                      f"    Requirement : {action.requirement}", f"    Reason      : {action.reason or action.description}",
                      f"    Depends on  : {deps}", f"    Risk        : {getattr(action.risk_level, 'value', action.risk_level)}",
                      f"    Confirmation: {confirm}"])
    lines.extend(["", "SUMMARY", f"{len(plan.actions)} actions",
                  f"{sum(a.requires_confirmation for a in plan.actions)} require confirmation",
                  f"{sum(a.action_type == ActionType.VERIFY for a in plan.actions)} automatic verification steps",
                  f"{sum(getattr(a.risk_level, 'value', a.risk_level) == 'BLOCKED' for a in plan.actions)} blocked"])
    return "\n".join(lines)
