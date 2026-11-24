from app.services import voice_service


def test_synthesize_returns_wav():
    audio, engine = voice_service.synthesize(
        "This is Metro Trust Bank. Stay on the line.",
        persona="caller",
    )
    assert audio[:4] == b"RIFF"
    assert engine in {"orpheus", "neural", "phone_fallback"}
    assert len(audio) > 1000


def test_speak_route(client):
    r = client.post(
        "/api/voice/speak",
        json={"text": "Please stay on the line.", "persona": "caller"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("audio/wav")
    assert r.content[:4] == b"RIFF"
