"""
RankForge CLI - Cache Module
==============================
File-based JSON cache with TTL support.
Stores API responses locally to reduce duplicate requests and costs.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger

logger = get_logger("rankforge.cache")


class Cache:
    """Simple file-based cache with time-to-live expiration."""

    def __init__(
        self,
        namespace: str = "default",
        ttl: Optional[int] = None,
    ):
        """
        Args:
            namespace: Sub-directory name for partitioning cached data.
            ttl: Time-to-live in seconds. Falls back to global setting.
        """
        self.enabled = settings.cache_enabled
        self.ttl = ttl or settings.cache_ttl_seconds
        self.cache_dir = Path(settings.cache_dir) / namespace
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ── Key Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _hash_key(key: str) -> str:
        """Create a filesystem-safe hash from an arbitrary key string."""
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{self._hash_key(key)}.json"

    # ── Public API ───────────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a cached value if it exists and hasn't expired.

        Returns:
            The cached data, or None on miss/expiry.
        """
        if not self.enabled:
            return None

        path = self._path(key)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                entry = json.load(f)

            if time.time() - entry.get("timestamp", 0) > self.ttl:
                path.unlink(missing_ok=True)
                logger.debug("Cache expired for key: %s", key[:60])
                return None

            logger.debug("Cache hit for key: %s", key[:60])
            return entry.get("data")
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Cache read error (%s): %s", key[:40], exc)
            return None

    def set(self, key: str, data: Any) -> None:
        """Store a value in the cache with the current timestamp."""
        if not self.enabled:
            return

        path = self._path(key)
        entry = {"timestamp": time.time(), "key_preview": key[:120], "data": data}

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, default=str)
            logger.debug("Cached key: %s", key[:60])
        except OSError as exc:
            logger.warning("Cache write error: %s", exc)

    def clear(self) -> int:
        """Remove all entries in this namespace. Returns count deleted."""
        count = 0
        for p in self.cache_dir.glob("*.json"):
            p.unlink(missing_ok=True)
            count += 1
        logger.info("Cleared %d cache entries from '%s'", count, self.cache_dir.name)
        return count
