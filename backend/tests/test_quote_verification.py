from app.schemas.analyze import AnalyzeResult, ReasonItem, RedFlag
from app.services.analyzer_service import analyze_text, verify_quotes


def test_quote_dropped_when_not_substring():
    result = AnalyzeResult(
        risk_level="likely_scam",
        headline="Looks risky",
        reasons=[
            ReasonItem(
                flag=RedFlag.URGENCY,
                quote="not in text",
                why="Pushes you to act fast.",
            )
        ],
    )
    out = verify_quotes("Your account will be locked today.", result)
    assert out.reasons == []
    assert out.risk_level == "cannot_tell"


def test_analyze_demo_keeps_matching_quotes():
    sample = (
        "This is Metro Trust Bank Fraud Unit. Your account will be closed in 20 minutes "
        "unless you share the one-time code we just sent. Do not tell anyone about this call."
    )
    result = analyze_text(sample)
    assert result.risk_level == "likely_scam"
    assert result.reasons
    for reason in result.reasons:
        assert reason.quote in sample


def test_analyze_demo_drops_bad_quotes_for_other_text():
    result = analyze_text("Hello friend, see you at tea on Sunday.")
    for reason in result.reasons:
        assert reason.quote in "Hello friend, see you at tea on Sunday."
