from memory.memory_utils import clean_duplicate_memories


def test_duplicate_cleanup_keeps_most_important_memory():
    user = {
        "souvenirs": [
            {"id": "s001", "contenu": "J'aime Python", "importance": "basse"},
            {"id": "s002", "contenu": " j'aime python ", "importance": "haute", "embedding": [1]},
        ]
    }

    assert clean_duplicate_memories(user) == 1
    assert user["souvenirs"] == [user["souvenirs"][0]]
    assert user["souvenirs"][0]["id"] == "s002"

