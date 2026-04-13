"""
RankForge CLI - Project Memory
================================
Persistent JSON-based storage for project results, history, and metadata.
Acts as a lightweight local database for all RankForge operations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger

logger = get_logger("rankforge.memory")


class ProjectMemory:
    """
    Simple JSON-backed project memory.

    Stores results keyed by category (keywords, backlinks, audits, etc.)
    with timestamps for history tracking.
    """

    def __init__(self, project_name: str = "default"):
        self.project_name = project_name
        self.data_dir = Path(settings.data_dir) / project_name
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.data_dir / "memory.json"
        self._data = self._load()

    # ── Persistence ──────────────────────────────────────────────────

    def _load(self) -> dict:
        """Load memory from disk."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load memory: %s", exc)
        return {"project": self.project_name, "created_at": datetime.now().isoformat(), "entries": {}}

    def _save(self) -> None:
        """Persist memory to disk."""
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, default=str, ensure_ascii=False)

    # ── CRUD Operations ──────────────────────────────────────────────

    def store(self, category: str, key: str, value: Any) -> None:
        """
        Store a result under category/key with a timestamp.

        Args:
            category: e.g. "keywords", "backlinks", "audits"
            key: Unique key within the category (e.g. domain or query)
            value: Any JSON-serializable data
        """
        if category not in self._data["entries"]:
            self._data["entries"][category] = {}

        self._data["entries"][category][key] = {
            "data": value,
            "stored_at": datetime.now().isoformat(),
        }
        self._save()
        logger.debug("Stored memory: %s/%s", category, key)

    def retrieve(self, category: str, key: str) -> Optional[Any]:
        """Retrieve a stored value, or None if not found."""
        entry = self._data.get("entries", {}).get(category, {}).get(key)
        return entry["data"] if entry else None

    def list_keys(self, category: str) -> list[str]:
        """List all keys in a category."""
        return list(self._data.get("entries", {}).get(category, {}).keys())

    def list_categories(self) -> list[str]:
        """List all categories that have stored data."""
        return list(self._data.get("entries", {}).keys())

    def delete(self, category: str, key: str) -> bool:
        """Delete a specific entry. Returns True if found and deleted."""
        entries = self._data.get("entries", {}).get(category, {})
        if key in entries:
            del entries[key]
            self._save()
            return True
        return False

    def get_history(self) -> dict:
        """Return the full memory structure (for debugging/export)."""
        return self._data
