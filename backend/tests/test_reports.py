import os

from app.config import get_settings


def test_summary_hidden_below_min(client, db_session):
    get_settings.cache_clear()
    os.environ["MIN_REPORTS_TO_SHOW"] = "3"
    client.post("/api/reports", json={"scam_type": "phone", "area": "england", "text": "test"})
    client.post("/api/reports", json={"scam_type": "phone", "area": "england", "text": "test2"})
    r = client.get("/api/reports/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["items"] == []


def test_summary_shows_at_min(client, db_session):
    get_settings.cache_clear()
    os.environ["MIN_REPORTS_TO_SHOW"] = "3"
    for i in range(3):
        client.post("/api/reports", json={"scam_type": "text", "area": "england", "text": f"n{i}"})
    r = client.get("/api/reports/summary")
    assert r.status_code == 200
    assert r.json()["total"] >= 3
    assert len(r.json()["items"]) >= 1