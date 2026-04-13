"""
RankForge CLI - Claude (Anthropic) Provider
=============================================
Integration with the Anthropic Messages API.
"""

from rankforge.ai.base import AIProvider
from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger

logger = get_logger("rankforge.ai.claude")

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ClaudeProvider(AIProvider):
    """Anthropic Claude integration."""

    def __init__(self):
        super().__init__("claude")

        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "The 'anthropic' package is required. Install with: pip install anthropic"
            )

        api_key = settings.anthropic_api_key
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Add it to your .env file."
            )

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = settings.default_ai_model_claude
        logger.info("Claude provider initialised (model: %s)", self.model)

    def generate_content(
        self,
        prompt: str,
        system: str = "You are an expert SEO consultant and content writer.",
        max_tokens: int = 8192,
    ) -> str:
        """
        Generate content using Claude's Messages API.

        Args:
            prompt: The user prompt.
            system: System-level instructions.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text content.
        """
        # Check cache first
        cache_key = f"claude:{self.model}:{system[:50]}:{prompt}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("Returning cached Claude response.")
            return cached

        # Rate limit
        self.limiter.acquire()

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.content[0].text

            # Cache the result
            self.cache.set(cache_key, result)
            logger.info("Claude generated %d chars.", len(result))
            return result

        except anthropic.APIStatusError as exc:
            logger.error("Claude API error: %s", exc.message)
            raise
        except Exception as exc:
            logger.error("Claude unexpected error: %s", exc)
            raise

    def chat(
        self,
        messages: list[dict],
        system: str = "You are an expert SEO consultant and content writer.",
        max_tokens: int = 8192,
    ) -> str:
        """
        Handle conversational turns using Claude's Messages API.

        Args:
            messages: List of message dictionaries containing "role" and "content".
            system: System-level instructions.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text content.
        """
        self.limiter.acquire()

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            result = response.content[0].text
            return result

        except Exception as exc:
            logger.error("Claude chat error: %s", exc)
            raise
