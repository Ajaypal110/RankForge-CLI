"""
RankForge CLI - Logging Module
===============================
Provides a configured logger with both console (Rich) and file handlers.
"""

import logging
import sys
from pathlib import Path

from rich.logging import RichHandler

from rankforge.config.settings import settings

# ── Module-level cache to avoid duplicate loggers ────────────────────
_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str = "rankforge") -> logging.Logger:
    """
    Return a named logger with Rich console output and rotating file output.

    Args:
        name: Logger name (dot-separated hierarchy supported).

    Returns:
        Configured logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Prevent duplicate handlers on re-import
    if not logger.handlers:
        # ── Rich console handler ─────────────────────────────────────
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            show_path=False,
        )
        console_handler.setLevel(logging.DEBUG)
        console_fmt = logging.Formatter("%(message)s", datefmt="[%X]")
        console_handler.setFormatter(console_fmt)
        logger.addHandler(console_handler)

        # ── File handler ─────────────────────────────────────────────
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger
