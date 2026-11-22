"""In-memory per-IP and per-user rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from app.config import get_settings


class RateLimiter:
    def __init__(self, limit_per_minute: int | None = None) -> None:
        settings = get_settings()
        self.limit = limit_per_minute or settings.rate_limit_per_minute
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _prune(self, key: str, now: float) -> None:
        window_start = now - 60.0
        self._buckets[key] = [t for t in self._buckets[key] if t > window_start]

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            self._prune(key, now)
            if len(self._buckets[key]) >= self.limit:
                return False
            self._buckets[key].append(now)
            return True

    def remaining(self, key: str) -> int:
        now = time.monotonic()
        with self._lock:
            self._prune(key, now)
            return max(0, self.limit - len(self._buckets[key]))


ip_limiter = RateLimiter()
user_limiter = RateLimiter()

_llm_settings = get_settings()
llm_limiter = RateLimiter(limit_per_minute=_llm_settings.rate_limit_llm_per_minute)