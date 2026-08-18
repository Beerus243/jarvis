import json

from config.settings import CONVERSATION_FILE, HISTORY_FILE, MEMORY_FILE


def test_data_paths_are_project_relative():
    assert MEMORY_FILE.name == "user.json"
    assert CONVERSATION_FILE.name == "conversation.json"
    assert HISTORY_FILE.name == "history.json"
    data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    assert isinstance(data.get("souvenirs"), list)

