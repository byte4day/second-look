from app.services.analyzer_service import analyze_text
from app.services.heuristics import scan, score


def test_bank_otp_heuristics():
    text = (
        "This is Metro Trust Bank Fraud Unit. Your account will be closed in 20 minutes "
        "unless you share the one-time code we just sent. Do not tell anyone about this call."
    )
    hits = scan(text)
    assert score(hits) >= 8
    flags = {h.flag.value for h in hits}
    assert "ASKS_FOR_CODE_OR_PASSWORD" in flags
    assert "SECRECY" in flags


def test_analyze_uses_heuristics_when_llm_quotes_fail(monkeypatch):
    text = "Send bitcoin now or police will arrest you. Keep this secret."

    class Boom:
        @staticmethod
        def chat_structured(*_a, **_k):
            raise RuntimeError("down")

    monkeypatch.setattr("app.services.analyzer_service.llm_gateway", Boom)
    result = analyze_text(text)
    assert result.risk_level in {"likely_scam", "suspicious"}
    assert result.reasons
    for r in result.reasons:
        assert r.quote in text


def test_probably_ok_harmless():
    text = "Hi Mum, I will bring milk when I visit on Sunday."
    hits = scan(text)
    assert score(hits) == 0


MARGARET = (
    "Metro Bank: your account has been LOCKED due to suspicious activity. Reply with the "
    "6-digit code we just sent within 30 minutes or your account will be closed. Call 0800 000 000."
)


def test_locked_account_code_request_is_likely_scam():
    from app.services import heuristics as h

    hits = h.scan(MARGARET)
    flags = {x.flag.value for x in hits}
    assert "ASKS_FOR_CODE_OR_PASSWORD" in flags
    assert h.risk_from_score(h.score(hits), MARGARET) == "likely_scam"


def test_quotes_never_cut_words():
    from app.services import heuristics as h

    for hit in h.scan(MARGARET):
        start = MARGARET.index(hit.quote)
        end = start + len(hit.quote)
        assert start == 0 or not MARGARET[start - 1].isalnum()
        assert end == len(MARGARET) or not MARGARET[end].isalnum()
