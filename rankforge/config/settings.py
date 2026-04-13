"""
RankForge CLI - Settings Module
================================
Centralized configuration management using Pydantic and python-dotenv.
Loads secrets from .env and provides typed access throughout the app.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application-wide configuration settings."""

    # ── AI Provider API Keys ──────────────────────────────────────────
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # ── Default AI Provider ───────────────────────────────────────────
    # Options: "openai", "claude", "gemini"
    default_ai_provider: str = "claude"
    default_ai_model_openai: str = "gpt-4o"
    default_ai_model_claude: str = "claude-sonnet-4-6"
    default_ai_model_gemini: str = "gemini-2.0-flash"

    # ── SEO API Keys ─────────────────────────────────────────────────
    serpapi_key: Optional[str] = None
    dataforseo_login: Optional[str] = None
    dataforseo_password: Optional[str] = None

    # ── Rate Limiting ────────────────────────────────────────────────
    rate_limit_requests_per_minute: int = 30
    rate_limit_burst: int = 5

    # ── Cache Settings ───────────────────────────────────────────────
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour default
    cache_dir: str = ".rankforge_cache"

    # ── Storage / Database ───────────────────────────────────────────
    data_dir: str = ".rankforge_data"
    export_dir: str = "exports"

    # ── Logging ──────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = "rankforge.log"

    # ── Scraping ─────────────────────────────────────────────────────
    scraper_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    scraper_timeout: int = 15
    scraper_max_retries: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton settings instance used across the application
settings = Settings()
