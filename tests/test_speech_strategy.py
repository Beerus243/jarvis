from voice.speech_strategy import select_speech


def test_strategy_preserves_meaning():
    text = "Le backend utilise FastAPI."
    assert select_speech(text, "question") == text
