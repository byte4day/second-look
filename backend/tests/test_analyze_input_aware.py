"""DEMO and live analyze must respect the input text."""

from app.services import analyzer_service


def test_harmless_text_is_not_forced_scam():
    result = analyzer_service.analyze_text("Hi mum, I will call you later about tea.")
    assert result.risk_level == "probably_ok"
    assert "scam" not in result.headline.lower() or "fine" in result.headline.lower()


def test_chase_fraud_sms_is_likely_scam():
    text = (
        "Chase Fraud: Did you write a check for $5,000.00? "
        "Please reply YES or NO. Msg & data rates may apply."
    )
    result = analyzer_service.analyze_text(text)
    assert result.risk_level in {"likely_scam", "suspicious"}
    assert result.reasons
    assert any("check" in r.quote.lower() or "chase" in r.quote.lower() for r in result.reasons)


def test_otp_bank_message_flags_code():
    result = analyzer_service.analyze_text(
        "Metro Trust Bank Fraud Unit. Share the one-time code. Do not tell anyone."
    )
    assert result.risk_level == "likely_scam"
    flags = {str(r.flag.value if hasattr(r.flag, "value") else r.flag) for r in result.reasons}
    assert "ASKS_FOR_CODE_OR_PASSWORD" in flags


def test_help_now_has_no_todo_stubs(client):
    body = client.get("/api/content/help-now?region=uk-example").json()
    blob = str(body).lower()
    assert "todo" not in blob
    phones = [c.get("phone") for c in body["who_to_contact"] if c.get("phone")]
    assert "0300 123 2040" in phones
