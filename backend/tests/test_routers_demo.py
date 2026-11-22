def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_scenarios(client):
    r = client.get("/api/scenarios")
    assert r.status_code == 200
    assert len(r.json()) >= 6


def test_analyze_text_demo(client):
    payload = {"text": "Your account locked. Read the 6-digit code."}
    r = client.post("/api/analyze/text", json=payload)
    assert r.status_code == 200
    assert r.json()["risk_level"] in {
        "likely_scam",
        "suspicious",
        "probably_ok",
        "cannot_tell",
    }


def test_drill_flow(client):
    body = {
        "scenario_id": "bank_otp",
        "difficulty": "easy",
        "mode": "experience",
    }
    r = client.post("/api/drills", json=body)
    assert r.status_code == 200
    sid = r.json()["id"]
    r2 = client.post(
        f"/api/drills/{sid}/turns",
        json={"message": "I will call my bank myself."},
    )
    assert r2.status_code == 200
    r3 = client.post(f"/api/drills/{sid}/finish", json={"hung_up": False})
    assert r3.status_code == 200
    assert "summary_plain" in r3.json()


def test_help_now(client):
    r = client.get("/api/content/help-now")
    assert r.status_code == 200
    body = r.json()
    assert "help_now_steps" in body
    assert "who_to_contact" in body
