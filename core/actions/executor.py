from .models import PCAction, ActionResult
from .screenshot import ScreenCapture

ALLOWED_ACTIONS = {"SCREENSHOT"}

def execute_pc_action(action: PCAction, *, capture=None):
    if not isinstance(action, PCAction) or action.action_type not in ALLOWED_ACTIONS:
        return ActionResult(getattr(action, "action_type", "UNKNOWN_ACTION"), False, "Action PC bloquée.", error="UNKNOWN_ACTION")
    return (capture or ScreenCapture()).capture()
