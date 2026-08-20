from voice.benchmark import benchmark


def test_benchmark_reports_generation_time():
    result = benchmark(type("Engine", (), {"generate": lambda self, text: "x.wav"})(), "Bonjour")
    assert result["audio_path"] == "x.wav"
    assert result["generation_seconds"] >= 0
