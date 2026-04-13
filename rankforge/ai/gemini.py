"""
RankForge CLI - Gemini (Google) Provider
==========================================
Integration with the Google Generative AI (Gemini) API.
"""

from rankforge.ai.base import AIProvider
from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger

logger = get_logger("rankforge.ai.gemini")

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiProvider(AIProvider):
    """Google Gemini integration."""

    def __init__(self):
        super().__init__("gemini")

        if not GEMINI_AVAILABLE:
            raise ImportError(
                "The 'google-generativeai' package is required. "
                "Install with: pip install google-generativeai"
            )

        api_key = settings.google_api_key
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set. Add it to your .env file.")

        genai.configure(api_key=api_key)
        self.model_name = settings.default_ai_model_gemini
        self.model = genai.GenerativeModel(self.model_name)
        logger.info("Gemini provider initialised (model: %s)", self.model_name)

    def generate_content(
        self,
        prompt: str,
        system: str = "You are an expert SEO consultant and content writer.",
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate content using Google Gemini API.

        Args:
            prompt: The user prompt.
            system: Prepended as context to the prompt.
            max_tokens: Max output tokens.

        Returns:
            Generated text content.
        """
        # Check cache first
        cache_key = f"gemini:{self.model_name}:{system[:50]}:{prompt}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("Returning cached Gemini response.")
            return cached

        # Rate limit
        self.limiter.acquire()

        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                ),
            )
            result = response.text

            # Cache the result
            self.cache.set(cache_key, result)
            logger.info("Gemini generated %d chars.", len(result))
            return result

        except Exception as exc:
            logger.error("Gemini error: %s", exc)
            raise
