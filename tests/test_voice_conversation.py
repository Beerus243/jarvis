from voice.conversation_loop import VoiceConversation


def test_voice_conversation_processes_multiple_turns_and_stops_locally():
    values = iter(["bonjour", "quelle heure est-il", "arrête-toi"])
    spoken = []
    conversation = VoiceConversation(
        listener=lambda: next(values),
        brain=lambda text: f"réponse: {text}",
        speaker=spoken.append,
        retry_delay=0,
    )

    results = conversation.run()

    assert len(results) == 2
    assert all(result["success"] for result in results)
    assert spoken == ["réponse: bonjour", "réponse: quelle heure est-il"]
    assert conversation._running is False


def test_voice_conversation_does_not_speak_empty_input():
    values = iter(["", "stop"])
    spoken = []
    conversation = VoiceConversation(
        listener=lambda: next(values),
        brain=lambda text: "ne doit pas être appelé",
        speaker=spoken.append,
        retry_delay=0,
    )

    assert conversation.run() == []
    assert spoken == []


def test_voice_conversation_handles_listener_error_without_crashing():
    calls = iter([RuntimeError("microphone indisponible"), "stop"])

    def listener():
        value = next(calls)
        if isinstance(value, Exception):
            raise value
        return value

    results = VoiceConversation(listener=listener, retry_delay=0).run()
    assert results[0]["success"] is False
    assert "microphone" in results[0]["error"]
