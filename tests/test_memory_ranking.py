from memory import find_semantic_memory


def test_project_and_preference_ranking():
    expected = {
        "Quelle technologie gère mon serveur ?": "FastAPI",
        "Quelle technologie utilise mon interface ?": "React",
        "Quelle est ma couleur préférée ?": "jaune",
        "Avec quel langage ai-je développé le projet ?": "Python",
        "Où sont stockées les données ?": "PostgreSQL",
    }

    for question, answer in expected.items():
        souvenir = find_semantic_memory(question)
        assert souvenir is not None
        assert answer.casefold() in souvenir["contenu"].casefold()


def test_unrelated_preference_is_rejected():
    assert find_semantic_memory("Qu'est-ce que j'aime regarder ?") is None

