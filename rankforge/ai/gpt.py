"""
RankForge CLI - GPT (OpenAI) Provider
========================================
Integration with the OpenAI Chat Completions API.
"""

from rankforge.ai.base import AIProvider
from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger

logger = get_logger("rankforge.ai.gpt")

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class GPTProvider(AIProvider):
    """OpenAI GPT integration."""

    def __init__(self):
        super().__init__("openai")

        if not OPENAI_AVAILABLE:
            raise ImportError(
                "The 'openai' package is required. Install with: pip install openai"
            )

        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set. Add it to your .env file.")

        self.client = openai.OpenAI(api_key=api_key)
        self.model = settings.default_ai_model_openai
        logger.info("GPT provider initialised (model: %s)", self.model)

    def generate_content(
        self,
        prompt: str,
        system: str = "You are an expert SEO consultant and content writer.",
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate content using OpenAI Chat Completions API.

        Args:
            prompt: The user prompt.
            system: System-level instructions.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text content.
        """
        # Check cache first
        cache_key = f"gpt:{self.model}:{system[:50]}:{prompt}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("Returning cached GPT response.")
            return cached

        # Rate limit
        self.limiter.acquire()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            result = response.choices[0].message.content

            # Cache the result
            self.cache.set(cache_key, result)
            logger.info("GPT generated %d chars.", len(result))
            return result

        except openai.APIStatusError as exc:
            logger.error("OpenAI API error: %s", exc.message)
            raise
        except Exception as exc:
            logger.error("GPT unexpected error: %s", exc)
            raise
