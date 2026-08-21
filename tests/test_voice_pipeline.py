from voice.voice_pipeline import VoicePipeline


def test_voice_pipeline_processes_one_turn():
    spoken = []
    pipeline = VoicePipeline(
        listener=lambda: "bonjour",
        brain=lambda text: f"Réponse à {text}",
        speaker=spoken.append,
    )

    result = pipeline.process_once()

    assert result == {
        "success": True,
        "input": "bonjour",
        "response": "Réponse à bonjour",
        "error": None,
    }
    assert spoken == ["Réponse à bonjour"]


def test_voice_pipeline_ignores_empty_input():
    brain = lambda text: (_ for _ in ()).throw(AssertionError("brain appelé"))
    result = VoicePipeline(listener=lambda: "", brain=brain).process_once()
    assert result["success"] is False
    assert result["error"] == "Aucune parole détectée"


def test_voice_pipeline_keeps_text_when_speaker_fails():
    def failing_speaker(response):
        raise RuntimeError("audio indisponible")

    result = VoicePipeline(
        listener=lambda: "bonjour",
        brain=lambda text: "Bonjour Fabrice.",
        speaker=failing_speaker,
    ).process_once()

    assert result["success"] is False
    assert result["response"] == "Bonjour Fabrice."
    assert "Erreur vocale" in result["error"]
