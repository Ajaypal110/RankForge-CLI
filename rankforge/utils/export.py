"""
RankForge CLI - Export Module
==============================
Export data to JSON and CSV files for downstream consumption.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger

logger = get_logger("rankforge.export")


class Exporter:
    """Write structured data to JSON or CSV files."""

    def __init__(self, sub_dir: str = ""):
        self.base_dir = Path(settings.export_dir)
        if sub_dir:
            self.base_dir = self.base_dir / sub_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _make_filename(self, prefix: str, ext: str) -> Path:
        """Generate a timestamped filename."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.base_dir / f"{prefix}_{ts}.{ext}"

    # ── JSON Export ──────────────────────────────────────────────────

    def to_json(self, data: Any, prefix: str = "export") -> Path:
        """
        Write data to a JSON file.

        Returns:
            Path to the created file.
        """
        path = self._make_filename(prefix, "json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        logger.info("Exported JSON -> %s", path)
        return path

    # ── CSV Export ────────────────────────────────────────────────────

    def to_csv(
        self,
        rows: list[dict[str, Any]],
        prefix: str = "export",
    ) -> Path:
        """
        Write a list of dicts to a CSV file.

        Returns:
            Path to the created file.
        """
        if not rows:
            logger.warning("No data to export to CSV.")
            return Path("")

        path = self._make_filename(prefix, "csv")
        fieldnames = list(rows[0].keys())

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info("Exported CSV (%d rows) -> %s", len(rows), path)
        return path
