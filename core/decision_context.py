"""Construction du contexte court utilisé pour prendre une décision."""

from core.conversation import get_context as load_conversation_context
from core.reference import analyze_reference, resolve_reference


def build_decision_context(message):
    history = load_conversation_context()[-10:]
    previous_user_message = None
    previous_assistant_message = None

    for item in reversed(history):
        role = item.get("role")
        content = item.get("message", "").strip()
        if not content:
            continue
        if previous_user_message is None and role == "user":
            previous_user_message = content
        if previous_assistant_message is None and role == "assistant":
            previous_assistant_message = content
        if previous_user_message and previous_assistant_message:
            break

    return {
        "message": message,
        "history": history,
        "previous_user_message": previous_user_message,
        "previous_assistant_message": previous_assistant_message,
        "reference": resolve_reference(message),
        "reference_info": analyze_reference(message, {
            "previous_user_message": previous_user_message,
        }),
        "previous_subject": {
            "reference": analyze_reference(message, {
                "previous_user_message": previous_user_message,
            }),
            "value": previous_assistant_message,
        } if previous_user_message or previous_assistant_message else None,
        "pc_context": _pc_context(),
    }


def _pc_context():
    from core.pc_context import get_pc_context
    return get_pc_context()
