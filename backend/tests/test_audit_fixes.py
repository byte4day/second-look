"""Regression tests for the backend audit fixes."""

from __future__ import annotations

import base64
import io
import subprocess
from unittest.mock import patch

from sqlalchemy import select

from app.models.entities import AuthCode, FamilyContact, User
from app.services import auth_service, rate_limit
from app.services.analyzer_service import analyze_text

ORIGIN = "http://localhost:5173"


# --- #1 wrong sign-in code is a 400, not a 500 ---------------------------------
def test_wrong_code_returns_400(client, db_session):
    auth_service.request_code(db_session, "a@example.com")
    r = client.post("/api/auth/verify-code", json={"email": "a@example.com", "code": "000000"})
    if r.status_code == 200:  # 1-in-a-million: the random code really was 000000
        return
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_code"


def test_unknown_email_returns_400(client):
    r = client.post("/api/auth/verify-code", json={"email": "nobody@example.com", "code": "123456"})
    assert r.status_code == 400


# --- #4 brute force: only newest code works, 5 wrong tries burns it ------------
def test_old_codes_retired_and_attempts_capped(db_session):
    email = "b@example.com"
    auth_service.request_code(db_session, email)
    first = db_session.scalar(select(AuthCode.code).where(AuthCode.email == email))
    auth_service.request_code(db_session, email)
    live = db_session.scalars(
        select(AuthCode).where(AuthCode.email == email, AuthCode.used.is_(False))
    ).all()
    assert len(live) == 1
    newest = live[0].code
    if first != newest:
        assert auth_service.verify_code(db_session, email, first) is None
    wrong = "111111" if newest != "111111" else "222222"
    for _ in range(auth_service.MAX_FAILED_ATTEMPTS):
        auth_service.verify_code(db_session, email, wrong)
    # Even the right code is refused after too many wrong guesses.
    assert auth_service.verify_code(db_session, email, newest) is None
    auth_service._reset_failures(email)


def test_forwarded_for_ignored_without_proxy():
    assert rate_limit.client_ip("1.2.3.4", "9.9.9.9", trust_proxy=False) == "1.2.3.4"
    assert rate_limit.client_ip("10.0.0.1", "9.9.9.9, 5.5.5.5", trust_proxy=True) == "5.5.5.5"


# --- #2 no-keyword scams are not "probably fine"; demo normal text still is ----
def test_new_number_money_request_not_probably_ok():
    r = analyze_text(
        "Hi Mum, lost my phone, this is my new number. Can you send £300 for rent today?"
    )
    assert r.risk_level in ("suspicious", "likely_scam")


def test_no_signal_but_not_everyday_is_cannot_tell():
    r = analyze_text("Please confirm your account details at your earliest convenience.")
    assert r.risk_level != "probably_ok"


def test_demo_normal_sample_still_probably_ok():
    r = analyze_text("Hi mum, I will call you later about Sunday lunch. Love you.")
    assert r.risk_level == "probably_ok"


def test_model_risk_never_lowered():
    from app.schemas.analyze import AnalyzeResult, ReasonItem
    from app.services.analyzer_service import _merge_heuristic_reasons, verify_quotes

    text = "Hello, your parcel is waiting. Reply to arrange delivery."
    model = AnalyzeResult(
        risk_level="likely_scam",
        headline="x",
        reasons=[ReasonItem(flag="URGENCY", quote="paraphrased words not in text", why="w")],
        what_to_do_now=[],
        what_not_to_do=[],
        note="",
    )
    merged = _merge_heuristic_reasons(text, verify_quotes(text, model))
    assert merged.risk_level == "likely_scam"


# --- #3 injection wording is flagged, not refused ------------------------------
def test_injection_words_flagged_as_scam():
    r = analyze_text(
        "Metro Trust Fraud Unit: criminals tried to steal money from you. "
        "Share the one-time code now."
    )
    assert r.risk_level in ("suspicious", "likely_scam")
    assert "cannot help" not in r.headline.lower()
    assert r.reasons


# --- #5 account deletion with contacts works; stale tokens rejected ------------
def test_delete_me_with_family_contact(client, db_session, auth_headers):
    r = client.post(
        "/api/family", json={"name": "Sam", "email": "sam@example.com"}, headers=auth_headers
    )
    assert r.status_code == 200
    r = client.delete("/api/me", headers=auth_headers)
    assert r.status_code == 200
    assert db_session.scalar(select(FamilyContact)) is None
    assert db_session.scalar(select(AuthCode).where(AuthCode.email == "user@example.com")) is None
    # The old token no longer works, even if a new user later gets the same id.
    db_session.add(User(id=1, email="new@example.com"))
    db_session.commit()
    r = client.get("/api/me", headers=auth_headers)
    assert r.status_code == 401


# --- #6 default JWT secret refused only outside demo mode ----------------------
def test_jwt_default_secret_refused_in_real_mode():
    import pytest

    from app.config import DEFAULT_JWT_SECRET, Settings, validate_settings

    validate_settings(Settings(_env_file=None, demo_mode=True, jwt_secret=DEFAULT_JWT_SECRET))
    with pytest.raises(RuntimeError):
        validate_settings(Settings(_env_file=None, demo_mode=False, jwt_secret=DEFAULT_JWT_SECRET))


# --- #7 espeak never receives user text as an argument -------------------------
def test_espeak_text_goes_to_stdin():
    from app.services import voice_service

    calls = []

    def fake_run(cmd, **kw):
        calls.append((cmd, kw))
        if "-w" in cmd:
            out = cmd[cmd.index("-w") + 1]
            open(out, "wb").write(b"RIFF")
        else:
            open(cmd[-1], "wb").write(b"RIFF")
        return subprocess.CompletedProcess(cmd, 0)

    with (
        patch.object(voice_service.shutil, "which", return_value="/usr/bin/espeak-ng"),
        patch.object(voice_service.subprocess, "run", side_effect=fake_run),
    ):
        voice_service._espeak_phone_wav("-f/etc/passwd", "caller")
    espeak_cmd, kw = calls[0]
    assert "-f/etc/passwd" not in espeak_cmd
    assert "--stdin" in espeak_cmd
    assert kw["input"] == b"-f/etc/passwd"


# --- #8 path traversal in scenario and region ----------------------------------
def test_scenario_path_traversal_is_404(client):
    for bad in ("../regions/generic", "/etc/passwd", "bank_otp/../../x"):
        r = client.post(
            "/api/drills", json={"scenario_id": bad, "difficulty": "easy", "mode": "experience"}
        )
        assert r.status_code in (404, 422), bad


def test_region_path_traversal_falls_back(client):
    r = client.get("/api/content/help-now", params={"region": "../scenarios/bank_otp"})
    assert r.status_code == 200
    assert "help_now_steps" in r.json()


# --- #11 decompression bomb is rejected before decoding ------------------------
def test_ocr_rejects_huge_canvas():
    from PIL import Image

    from app.services import ocr_service

    buf = io.BytesIO()
    Image.new("1", (6000, 6000), 1).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    assert ocr_service.extract_text(b64, "image/png") == ""


# --- #13 report fields are fixed lists -----------------------------------------
def test_report_free_text_category_rejected(client):
    r = client.post(
        "/api/reports",
        json={"scam_type": "Call 0800-111-222 for refund", "area": "england"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_input"


# --- #15 CORS headers on 429 and preflight does not spend budget ---------------
def test_rate_limit_response_has_cors_and_preflight_is_free(client):
    rate_limit.reset_all_for_tests()
    try:
        with patch.object(rate_limit, "llm_limiter") as lim:
            lim.return_value = rate_limit.RateLimiter(limit_per_minute=1)
            pre = client.options(
                "/api/analyze/text",
                headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"},
            )
            assert pre.status_code == 200
            ok = client.post(
                "/api/analyze/text", json={"text": "hello there"}, headers={"Origin": ORIGIN}
            )
            assert ok.status_code == 200  # preflight did not use the single slot
            blocked = client.post(
                "/api/analyze/text", json={"text": "hello again"}, headers={"Origin": ORIGIN}
            )
            assert blocked.status_code == 429
            assert blocked.headers.get("access-control-allow-origin") == ORIGIN
    finally:
        rate_limit.reset_all_for_tests()


def test_chunked_body_over_limit_is_413(client):
    from app import main

    def gen():
        chunk = b"x" * (1024 * 1024)
        for _ in range(6):
            yield chunk

    r = client.post(
        "/api/analyze/text",
        content=gen(),
        headers={"content-type": "application/json", "Origin": ORIGIN},
    )
    assert r.status_code == 413
    assert main.MAX_BODY == 5 * 1024 * 1024
    assert r.headers.get("access-control-allow-origin") == ORIGIN
