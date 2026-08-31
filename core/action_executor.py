"""Exécution contrôlée des actions locales de JARVIS."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime

from config.settings import MEMORY_FILE
from core.action_policy import BLOCKED_ACTION, CONFIRMATION_REQUIRED, classify_action
from core.dispatcher import dispatch


@dataclass
class ActionResult:
    success: bool
    action: str
    message: str
    error: str | None = None
    policy: str = BLOCKED_ACTION
    confirmation: bool = False
    artifact_path: str | None = None


def _log(result):
    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        data = {}
    logs = data.setdefault("action_history", [])
    logs.append({"action": result.action, "timestamp": datetime.now().astimezone().isoformat(), "result": result.message, "success": result.success, "confirmation": result.confirmation, "error": result.error})
    data["action_history"] = logs[-50:]
    try:
        with MEMORY_FILE.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    except OSError:
        pass


def execute_action(action, confirmation=False, dispatcher=None):
    action_id = action.get("action") if isinstance(action, dict) else action
    policy = classify_action(action_id)
    if policy == BLOCKED_ACTION:
        result = ActionResult(False, action_id, "Cette action est bloquée par la politique de sécurité.", policy=policy)
    elif policy == CONFIRMATION_REQUIRED and not confirmation:
        result = ActionResult(False, action_id, "Cette action nécessite une confirmation explicite.", policy=policy)
    else:
        try:
            response = (dispatcher or dispatch)(action)
            if hasattr(response, "success") and hasattr(response, "message"):
                result = ActionResult(bool(response.success), action_id, response.message, error=response.error,
                                      policy=policy, confirmation=confirmation, artifact_path=getattr(response, "artifact_path", None))
            else:
                ok, message = response if isinstance(response, tuple) else (bool(response), response)
                result = ActionResult(bool(ok), action_id, message or "L'action n'a pas produit de résultat.", error=None if ok else "Aucun résultat", policy=policy, confirmation=confirmation)
        except Exception as error:
            result = ActionResult(False, action_id, "L'action a échoué.", error=str(error), policy=policy, confirmation=confirmation)
    _log(result)
    return result


def result_dict(result):
    return asdict(result)


def execute_plan(actions, confirmation=False, dispatcher=None):
    """Exécute séquentiellement un plan déjà construit.

    L'exécution s'arrête dès qu'une étape est bloquée, demande confirmation
    ou échoue. Aucune boucle ni reprise implicite n'est créée.
    """

    results = []

    for item in actions or []:

        # Conserver le dictionnaire complet lorsqu'il s'agit
        # d'une action structurée.
        if isinstance(item, dict):
            action = item

        elif hasattr(item, "action"):
            action = item.action

            # ------------------------------------------------
            # PlannedAction
            # ------------------------------------------------
            # Certaines actions composées transportent une
            # cible dans "message".
            #
            # Exemple :
            #
            # PlannedAction(
            #     "OPEN_VSCODE",
            #     "~/dev/jarvis"
            # )
            #
            # doit devenir :
            #
            # {
            #     "action": "OPEN_VSCODE",
            #     "target": "~/dev/jarvis"
            # }
            #
            # On ne modifie que les actions qui nécessitent
            # explicitement cette cible.
            # ------------------------------------------------

            if action == "OPEN_VSCODE" and getattr(item, "message", ""):
                action = {
                    "action": "OPEN_VSCODE",
                    "target": item.message,
                }

        else:
            action = item

        result = execute_action(
            action,
            confirmation=confirmation,
            dispatcher=dispatcher,
        )

        results.append(result)

        if (
            not result.success
            or result.policy in {
                BLOCKED_ACTION,
                CONFIRMATION_REQUIRED,
            }
        ):
            break

    return results
