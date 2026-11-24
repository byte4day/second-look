"""In-memory per-IP and per-user rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from app.config import get_settings


class RateLimiter:
    def __init__(self, limit_per_minute: int = 60) -> None:
        self.limit = max(1, int(limit_per_minute))
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _prune(self, key: str, now: float) -> None:
        window_start = now - 60.0
        kept = [t for t in self._buckets.get(key, ()) if t > window_start]
        if kept:
            self._buckets[key] = kept
        else:
            self._buckets.pop(key, None)
        self._sweep(now)

    def _sweep(self, now: float) -> None:
        """Drop idle keys so memory does not grow with every IP ever seen."""
        if len(self._buckets) < 1024:
            return
        window_start = now - 60.0
        for k in [k for k, v in self._buckets.items() if not v or v[-1] <= window_start]:
            self._buckets.pop(k, None)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            self._prune(key, now)
            if len(self._buckets.get(key, ())) >= self.limit:
                return False
            self._buckets[key].append(now)
            return True

    def remaining(self, key: str) -> int:
        now = time.monotonic()
        with self._lock:
            self._prune(key, now)
            return max(0, self.limit - len(self._buckets.get(key, ())))

    def retry_after_seconds(self, key: str) -> int:
        now = time.monotonic()
        with self._lock:
            self._prune(key, now)
            if not self._buckets.get(key):
                return 1
            oldest = min(self._buckets[key])
            return max(1, int(60 - (now - oldest)) + 1)

    def reset_for_tests(self) -> None:
        with self._lock:
            self._buckets.clear()


def client_ip(host: str | None, forwarded_for: str | None, trust_proxy: bool | None = None) -> str:
    """Client IP for limits. X-Forwarded-For is only trusted behind a configured proxy,
    otherwise anyone could pick a fresh fake IP per request and skip every limit."""
    if trust_proxy is None:
        trust_proxy = get_settings().trust_proxy_headers
    if trust_proxy and forwarded_for:
        # The proxy appends the real client address as the last hop.
        hops = [h.strip() for h in forwarded_for.split(",") if h.strip()]
        if hops:
            return hops[-1]
    return host or "unknown"


_lock = Lock()
_ip: RateLimiter | None = None
_user: RateLimiter | None = None
_llm: RateLimiter | None = None


def ip_limiter() -> RateLimiter:
    global _ip
    with _lock:
        if _ip is None:
            _ip = RateLimiter(get_settings().rate_limit_per_minute)
        return _ip


def user_limiter() -> RateLimiter:
    global _user
    with _lock:
        if _user is None:
            _user = RateLimiter(get_settings().rate_limit_per_minute)
        return _user


def llm_limiter() -> RateLimiter:
    global _llm
    with _lock:
        if _llm is None:
            _llm = RateLimiter(get_settings().rate_limit_llm_per_minute)
        return _llm


def reset_all_for_tests() -> None:
    global _ip, _user, _llm
    with _lock:
        _ip = _user = _llm = None
