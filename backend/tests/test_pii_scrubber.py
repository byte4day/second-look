from app.services import pii_scrubber


def test_scrub_email_phone_url():
    text = "Call 07123456789 or email me@evil.com http://bad.test and card 4111 1111 1111 1111"
    out = pii_scrubber.scrub(text)
    assert "@" not in out
    assert "http" not in out
    assert "07123456789" not in out