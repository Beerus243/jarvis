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
    policy = classify_action(action)
    if policy == BLOCKED_ACTION:
        result = ActionResult(False, action, "Cette action est bloquée par la politique de sécurité.", policy=policy)
    elif policy == CONFIRMATION_REQUIRED and not confirmation:
        result = ActionResult(False, action, "Cette action nécessite une confirmation explicite.", policy=policy)
    else:
        try:
            response = (dispatcher or dispatch)(action)
            result = ActionResult(bool(response), action, response or "L'action n'a pas produit de résultat.", error=None if response else "Aucun résultat", policy=policy, confirmation=confirmation)
        except Exception as error:
            result = ActionResult(False, action, "L'action a échoué.", error=str(error), policy=policy, confirmation=confirmation)
    _log(result)
    return result


def result_dict(result):
    return asdict(result)
