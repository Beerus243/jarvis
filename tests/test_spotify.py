from tools import spotify


def test_search_query():
    captured = {}

    def fake_request(method, endpoint, **kwargs):
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["params"] = kwargs["params"]

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "tracks": {
                        "items": [
                            {
                                "name": "Mosaïque Solitaire",
                                "uri": "spotify:track:test",
                                "artists": [
                                    {
                                        "name": "Damso"
                                    }
                                ],
                            }
                        ]
                    }
                }

        return Response()

    original = spotify._request

    try:
        spotify._request = fake_request

        result = spotify.search_track(
            title="Mosaïque Solitaire",
            artist="Damso",
        )

        assert result["uri"] == "spotify:track:test"
        assert (
            captured["params"]["type"]
            == "track"
        )

    finally:
        spotify._request = original


def test_play_track(monkeypatch):
    calls = []

    def fake_search_track(title=None, artist=None):
        return {
            "name": "Mosaïque Solitaire",
            "uri": "spotify:track:test",
            "artists": [
                {
                    "name": "Damso"
                }
            ],
        }

    def fake_device():
        return {
            "id": "device-test",
            "is_active": True,
        }

    def fake_request(method, endpoint, **kwargs):
        calls.append(
            (
                method,
                endpoint,
                kwargs,
            )
        )

        class Response:
            status_code = 204

        return Response()

    monkeypatch.setattr(
        spotify,
        "search_track",
        fake_search_track,
    )

    monkeypatch.setattr(
        spotify,
        "get_active_device",
        fake_device,
    )

    monkeypatch.setattr(
        spotify,
        "_request",
        fake_request,
    )

    success, message = spotify.play_track(
        title="Mosaïque Solitaire",
        artist="Damso",
    )

    assert success is True
    assert "Mosaïque Solitaire" in message

    assert calls[0][0] == "PUT"
    assert calls[0][1] == "/me/player/play"
    assert calls[0][2]["json"]["uris"] == [
        "spotify:track:test"
    ]