"""
RankForge CLI - Rate Limiter
==============================
Token-bucket rate limiter to protect against API throttling.
"""

import time
import threading
from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger

logger = get_logger("rankforge.rate_limiter")


class RateLimiter:
    """
    Thread-safe token-bucket rate limiter.

    Usage:
        limiter = RateLimiter(rpm=30, burst=5)
        limiter.acquire()  # blocks until a token is available
    """

    def __init__(
        self,
        rpm: int | None = None,
        burst: int | None = None,
    ):
        self.rpm = rpm or settings.rate_limit_requests_per_minute
        self.burst = burst or settings.rate_limit_burst
        self.interval = 60.0 / self.rpm  # seconds between tokens
        self.tokens = float(self.burst)
        self.max_tokens = float(self.burst)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """Add tokens based on elapsed time since last refill."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed / self.interval
        self.tokens = min(self.max_tokens, self.tokens + new_tokens)
        self.last_refill = now

    def acquire(self) -> None:
        """
        Block until a token is available, then consume one.
        Logs a warning when the caller must wait.
        """
        while True:
            with self._lock:
                self._refill()
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                wait_time = self.interval - (time.monotonic() - self.last_refill)

            if wait_time > 0.05:
                logger.debug("Rate limiter: waiting %.2fs", wait_time)
            time.sleep(max(wait_time, 0.01))
