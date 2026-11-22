from sqlalchemy import select

from app.models.entities import Invitation


def test_double_optin(client, auth_headers, db_session):
    r = client.post(
        "/api/family",
        json={"name": "Alex", "email": "alex@example.com"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "waiting"
    contact_id = r.json()["id"]

    bad = client.post("/api/family/invitations/badtoken/accept")
    assert bad.status_code == 400

    inv = db_session.execute(select(Invitation)).scalar_one()
    good = client.post(f"/api/family/invitations/{inv.token}/accept")
    assert good.status_code == 200
    assert good.json()["status"] == "accepted"

    listed = client.get("/api/family", headers=auth_headers)
    assert listed.json()[0]["status"] == "accepted"

    del_r = client.delete(f"/api/family/{contact_id}", headers=auth_headers)
    assert del_r.status_code == 200

def test_alert_skipped_for_waiting_contact(client, auth_headers, db_session):
    client.post(
        "/api/family",
        json={"name": "Sam", "email": "sam@example.com"},
        headers=auth_headers,
    )
    r = client.post(
        "/api/alerts",
        json={"message_plain": "Need help", "contact_ids": []},
        headers=auth_headers,
    )
    # No accepted contacts yet — sent should be 0
    assert r.status_code == 200
    body = r.json()
    assert body.get("sent", 0) == 0
