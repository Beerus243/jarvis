from voice.audio_capture import (
    CaptureConfig,
    analyze_audio,
    calculate_speech_threshold,
    clipping_percent,
    peak,
    rms,
)


def pcm(*values):
    import struct
    return struct.pack("<" + "h" * len(values), *values)


def test_rms_peak_and_clipping():
    data = pcm(0, 3, -4, 32767)
    assert round(rms(data), 2) == 16383.5
    assert peak(data) == 32767
    assert clipping_percent(data) == 25.0


def test_empty_audio_is_safe():
    assert analyze_audio(b"", CaptureConfig()) == {
        "audio": b"",
        "duration": 0.0,
        "rms": 0.0,
        "peak": 0,
        "clipping": 0.0,
        "speech_detected": False,
    }


def test_analyze_audio_duration_and_signal():
    config = CaptureConfig(sample_rate=4)
    result = analyze_audio(pcm(100, -100, 0, 0), config)
    assert result["duration"] == 1.0
    assert result["rms"] == 70.71067811865476
    assert result["peak"] == 100


def test_config_exposes_endpointing_parameters():
    config = CaptureConfig()
    assert config.pre_roll == 0.25
    assert config.start_frames == 2
    assert config.silence_duration == 0.8
    assert config.minimum_speech == 0.3
    assert config.maximum_duration == 8.0


def test_threshold_uses_median_for_variable_noise():
    threshold, floor = calculate_speech_threshold([100, 110, 120, 130, 5000])
    assert floor == 120
    assert threshold == 300


def test_threshold_respects_configured_multiplier():
    threshold, floor = calculate_speech_threshold(
        [400, 420, 440], multiplier=1.5, minimum_threshold=0
    )
    assert floor == 420
    assert threshold == 630


def test_threshold_detects_weak_and_strong_voice_without_noise_trigger():
    threshold, _ = calculate_speech_threshold(
        [100, 110, 120, 130], multiplier=1.5, minimum_threshold=0
    )
    assert max([100, 110, 120, 130]) <= threshold
    assert 250 > threshold
    assert 2000 > threshold


def test_capture_command_calibrates_noise_and_accepts_quieter_speech():
    from types import SimpleNamespace
    from voice.audio_capture import capture_command

    config = CaptureConfig(
        sample_rate=100,
        chunk=10,
        calibration_duration=0.2,
        pre_roll=0.2,
        wait_timeout=0.5,
        maximum_duration=1.0,
        silence_duration=0.2,
        minimum_speech=0.1,
        minimum_threshold=80,
        threshold_multiplier=1.5,
    )
    frames = [
        pcm(*([20] * 10)), pcm(*([20] * 10)),
        pcm(*([100] * 10)), pcm(*([100] * 10)),
        pcm(*([0] * 10)), pcm(*([0] * 10)),
    ]
    stream = SimpleNamespace(read=lambda count, **kwargs: frames.pop(0))

    result = capture_command(stream, config)

    assert result['speech_detected'] is True
    assert result['threshold'] == 80
    assert result['noise_floor'] == 20
    assert result['duration'] > 0


def test_capture_command_can_reuse_noise_floor_without_waiting_for_calibration():
    from types import SimpleNamespace
    from voice.audio_capture import capture_command

    config = CaptureConfig(sample_rate=100, chunk=10, wait_timeout=0.5,
                           maximum_duration=1.0, silence_duration=0.2,
                           minimum_speech=0.1, minimum_threshold=80)
    frames = [pcm(*([100] * 10)), pcm(*([100] * 10)), pcm(*([0] * 10))]
    stream = SimpleNamespace(read=lambda count, **kwargs: frames.pop(0))

    result = capture_command(stream, config, noise_floor=20)

    assert result['speech_detected'] is True
    assert result['noise_floor'] == 20
