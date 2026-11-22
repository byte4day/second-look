from app.services.rate_limit import RateLimiter


def test_rate_limiter_blocks():
    rl = RateLimiter(limit_per_minute=2)
    assert rl.allow("a")
    assert rl.allow("a")
    assert not rl.allow("a")
    assert rl.allow("b")