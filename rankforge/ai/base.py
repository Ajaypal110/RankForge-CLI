"""
RankForge CLI - AI Base Provider
==================================
Abstract base class and factory for AI providers.
All providers share a common interface so they're easily swappable.
"""

from abc import ABC, abstractmethod
from typing import Optional

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger
from rankforge.utils.cache import Cache
from rankforge.utils.rate_limiter import RateLimiter

logger = get_logger("rankforge.ai")


class AIProvider(ABC):
    """Abstract base class for all AI provider integrations."""

    def __init__(self, name: str):
        self.name = name
        self.cache = Cache(namespace=f"ai_{name}")
        self.limiter = RateLimiter()

    # ── Core Methods (must implement) ────────────────────────────────

    @abstractmethod
    def generate_content(self, prompt: str, system: str = "", max_tokens: int = 2048) -> str:
        """Generate free-form content from a prompt."""
        ...

    @abstractmethod
    def chat(self, messages: list[dict], system: str = "", max_tokens: int = 4096) -> str:
        """Handle conversational turns via a list of message dicts.
        Format: [{"role": "user", "content": "..."}]
        """
        ...

    # ── SEO-Specific Convenience Methods ─────────────────────────────

    def generate_outreach_email(
        self,
        target_site: str,
        your_site: str,
        topic: str,
        tone: str = "professional",
    ) -> str:
        """Generate a personalised outreach email for link building."""
        prompt = (
            f"Write a {tone} outreach email to the owner of {target_site}. "
            f"I run {your_site} and I'd like to propose a guest post or link exchange "
            f"related to '{topic}'. Keep it concise (under 200 words), friendly, "
            f"and persuasive. Include a compelling subject line at the top."
        )
        return self.generate_content(prompt)

    def generate_seo_meta(self, page_title: str, page_content_summary: str) -> str:
        """Generate an SEO-optimised meta title + description pair."""
        prompt = (
            f"Generate an SEO-optimised meta title (max 60 chars) and meta description "
            f"(max 155 chars) for a page titled '{page_title}'. "
            f"Summary of page content: {page_content_summary}\n\n"
            f"Return in this exact format:\n"
            f"Meta Title: ...\nMeta Description: ..."
        )
        return self.generate_content(prompt)

    def generate_anchor_text(self, target_url: str, context: str, count: int = 5) -> str:
        """Suggest natural anchor text variations for a backlink."""
        prompt = (
            f"Suggest {count} natural, diverse anchor text variations for linking to "
            f"{target_url} within content about '{context}'. Return as a numbered list. "
            f"Mix branded, generic, exact-match, and partial-match anchors."
        )
        return self.generate_content(prompt)

    def generate_article(self, topic: str, word_count: int = 1500) -> str:
        """Generate an SEO-optimised long-form article."""
        prompt = (
            f"Write an SEO-optimised, engaging article about '{topic}'. "
            f"Target length: ~{word_count} words. Include:\n"
            f"- A compelling H1 title\n"
            f"- Subheadings (H2/H3) for structure\n"
            f"- Introduction with hook\n"
            f"- Actionable content with examples\n"
            f"- A conclusion with a CTA\n"
            f"- Natural keyword usage (no stuffing)\n\n"
            f"Write in markdown format."
        )
        return self.generate_content(prompt, max_tokens=4096)


def get_ai_provider(provider_name: Optional[str] = None) -> AIProvider:
    """
    Factory function: returns the requested (or default) AI provider instance.

    Args:
        provider_name: "openai", "claude", or "gemini". Falls back to settings.

    Returns:
        An initialized AIProvider subclass.
    """
    name = (provider_name or settings.default_ai_provider).lower()

    if name in ("openai", "gpt"):
        from rankforge.ai.gpt import GPTProvider
        return GPTProvider()
    elif name in ("claude", "anthropic"):
        from rankforge.ai.claude import ClaudeProvider
        return ClaudeProvider()
    elif name == "gemini":
        from rankforge.ai.gemini import GeminiProvider
        return GeminiProvider()
    else:
        raise ValueError(
            f"Unknown AI provider '{name}'. Choose from: openai, claude, gemini"
        )
