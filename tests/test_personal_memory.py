import json

from memory import personal_memory


def write_memory(path, **overrides):
    data = {
        "identite": {"name": "Fabrice", "postnom": "Malanga"},
        "preferences": {"couleur_preferee": "jaune"},
        "memory": {"aime_regarder": "des films et des animés"},
    }
    data.update(overrides)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_identity(tmp_path, monkeypatch):
    path = tmp_path / "user.json"
    write_memory(path)
    monkeypatch.setattr(personal_memory, "MEMORY_FILE", path)

    assert personal_memory.answer_personal_question("qui suis-je") == (
        "Tu es Fabrice Malanga."
    )


def test_favorite_color(tmp_path, monkeypatch):
    path = tmp_path / "user.json"
    write_memory(path)
    monkeypatch.setattr(personal_memory, "MEMORY_FILE", path)

    assert personal_memory.answer_personal_question(
        "quelle est ma couleur préférée"
    ) == "Ta couleur préférée est jaune."


def test_favorite_content(tmp_path, monkeypatch):
    path = tmp_path / "user.json"
    write_memory(path)
    monkeypatch.setattr(personal_memory, "MEMORY_FILE", path)

    assert personal_memory.answer_personal_question(
        "qu'est-ce que j'aime regarder"
    ) == "Tu aimes regarder des films et des animés."


def test_watching_preference_is_saved_locally(tmp_path, monkeypatch):
    path = tmp_path / "user.json"
    write_memory(path, memory={})
    monkeypatch.setattr(personal_memory, "MEMORY_FILE", path)

    response = personal_memory.answer_personal_question(
        "J'aime regarder des films et des animés"
    )

    assert response == "Je retiens que tu aimes regarder des films et des animés."
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["memory"]["aime_regarder"] == "des films et des animés"


def test_personal_question_does_not_call_groq(tmp_path, monkeypatch):
    path = tmp_path / "user.json"
    write_memory(path)
    monkeypatch.setattr(personal_memory, "MEMORY_FILE", path)

    from core import brain

    monkeypatch.setattr(brain, "add_message", lambda *args: None)
    monkeypatch.setattr(
        brain,
        "ask_ai",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Groq ne doit pas être appelé")
        ),
    )

    assert brain.think("quelle est ma couleur préférée") == (
        "Ta couleur préférée est jaune."
    )

