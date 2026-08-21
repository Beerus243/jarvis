from memory import memory as memory_module


def test_project_and_preference_ranking(monkeypatch):
    souvenirs = [
        {"contenu": "Le serveur utilise FastAPI."},
        {"contenu": "L'interface utilise React."},
    ]
    monkeypatch.setattr(memory_module, "load_memory", lambda: {"souvenirs": souvenirs})
    monkeypatch.setattr(
        memory_module,
        "calculate_hybrid_score",
        lambda question, souvenir: {
            "souvenir": souvenir,
            "final": 0.9 if ("serveur" in question.lower()) == ("serveur" in souvenir["contenu"].lower()) else 0.1,
        },
    )
    result = memory_module.find_semantic_memory("Quelle technologie gère mon serveur ?")
    assert result["contenu"] == "Le serveur utilise FastAPI."


def test_unrelated_preference_is_rejected(monkeypatch):
    monkeypatch.setattr(memory_module, "load_memory", lambda: {"souvenirs": []})
    assert memory_module.find_semantic_memory("Qu'est-ce que j'aime regarder ?") is None
