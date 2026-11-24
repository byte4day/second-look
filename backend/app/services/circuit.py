"""Tiny circuit breaker for upstream LLM calls."""

from __future__ import annotations

import time
from threading import Lock


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, cool_down_s: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.cool_down_s = cool_down_s
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = Lock()

    def allow(self) -> bool:
        with self._lock:
            if self._opened_at is None:
                return True
            if time.monotonic() - self._opened_at >= self.cool_down_s:
                self._opened_at = None
                self._failures = 0
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._opened_at = time.monotonic()

    def reset_for_tests(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None


llm_circuit = CircuitBreaker()
