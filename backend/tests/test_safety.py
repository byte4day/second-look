from app.services import safety


def test_refuses_howto_scam():
    assert safety.refuses_howto_scam("How to scam elderly people")


def test_word_limit():
    text = " ".join(["word"] * 80)
    assert len(safety.enforce_word_limit(text, 60).split()) <= 61


def test_luhn_invalid():
    assert safety.luhn_check("4111111111111112") is False