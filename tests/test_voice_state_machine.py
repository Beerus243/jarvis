from voice.assistant_loop import AssistantLoop, LISTENING, SLEEPING, THINKING, SPEAKING


def test_voice_state_machine_uses_brain_and_returns_to_sleep():
    values = iter(["Jarvis", "quelle heure est-il"])
    states = []
    spoken = []
    loop = AssistantLoop(
        listener=lambda: next(values),
        speaker=spoken.append,
        brain=lambda text: (states.append(loop.state), "Il est midi")[1],
        retry_delay=0,
    )

    result = loop.run(max_cycles=1)

    assert result[0]["response"] == "Il est midi"
    assert spoken == ["Je vous écoute.", "Il est midi"]
    assert states == [THINKING]
    assert loop.state == SLEEPING


def test_voice_state_machine_does_not_activate_without_wake_word():
    values = iter(["bonjour"])
    loop = AssistantLoop(listener=lambda: next(values), retry_delay=0)
    assert loop.run(max_cycles=1) == []
    assert loop.state == SLEEPING
