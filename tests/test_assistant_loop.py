from voice.assistant_loop import AssistantLoop, SLEEPING, STOPPED


def test_assistant_loop_wakes_thinks_speaks_and_returns_to_sleep():
    values = iter(["bonjour", "Hey Jarvis", "quelle heure est-il", "bonjour"])
    spoken = []
    loop = AssistantLoop(
        listener=lambda: next(values),
        speaker=spoken.append,
        brain=lambda text: f"réponse: {text}",
        retry_delay=0,
    )

    results = loop.run(max_cycles=3)

    assert results[0]["success"] is True
    assert results[0]["input"] == "quelle heure est-il"
    assert spoken == ["Je vous écoute.", "réponse: quelle heure est-il"]
    assert loop.state == SLEEPING


def test_assistant_loop_ignores_speech_without_wake_word():
    values = iter(["bonjour", "jardin", "Jarvis", "stop"])
    spoken = []
    loop = AssistantLoop(
        listener=lambda: next(values),
        speaker=spoken.append,
        brain=lambda text: "réponse",
        retry_delay=0,
    )

    results = loop.run()

    assert results == []
    assert spoken == ["Je vous écoute."]
    assert loop.state == STOPPED
