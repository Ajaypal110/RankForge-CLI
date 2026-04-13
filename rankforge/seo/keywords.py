"""
RankForge CLI - Keyword Research Module
=========================================
Keyword research via Google Autocomplete, SerpAPI, and AI-powered expansion.
Returns structured data with search volume estimates and difficulty scores.
"""

import json
import re
from typing import Any, Optional

import httpx

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger
from rankforge.utils.cache import Cache
from rankforge.utils.rate_limiter import RateLimiter
from rankforge.utils.display import Display

logger = get_logger("rankforge.seo.keywords")


class KeywordResearcher:
    """
    Multi-source keyword research engine.

    Sources:
        1. Google Autocomplete API (free, no key required)
        2. SerpAPI (if key configured)
        3. AI-based keyword expansion (via any configured AI provider)
    """

    def __init__(self):
        self.cache = Cache(namespace="keywords")
        self.limiter = RateLimiter()
        self.client = httpx.Client(
            headers={"User-Agent": settings.scraper_user_agent},
            timeout=settings.scraper_timeout,
            follow_redirects=True,
        )

    # ── Google Autocomplete ──────────────────────────────────────────

    def google_autocomplete(self, query: str, language: str = "en") -> list[str]:
        """
        Fetch keyword suggestions from Google Autocomplete.

        Args:
            query: Seed keyword.
            language: Language code (default: en).

        Returns:
            List of suggested keyword strings.
        """
        cache_key = f"autocomplete:{language}:{query}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        self.limiter.acquire()

        url = "https://suggestqueries.google.com/complete/search"
        params = {"client": "firefox", "q": query, "hl": language}

        try:
            resp = self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            suggestions = data[1] if len(data) > 1 else []
            self.cache.set(cache_key, suggestions)
            logger.info("Autocomplete returned %d suggestions for '%s'", len(suggestions), query)
            return suggestions
        except Exception as exc:
            logger.error("Google Autocomplete error: %s", exc)
            return []

    # ── SerpAPI Integration ──────────────────────────────────────────

    def serpapi_keywords(self, query: str, location: str = "United States") -> dict[str, Any]:
        """
        Fetch keyword data from SerpAPI (Google search results + related).

        Requires SERPAPI_KEY in .env.

        Returns:
            Dict with related_searches, related_questions, organic_count.
        """
        if not settings.serpapi_key:
            logger.warning("SERPAPI_KEY not set -- skipping SerpAPI lookup.")
            return {"error": "SERPAPI_KEY not configured"}

        cache_key = f"serpapi:{location}:{query}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        self.limiter.acquire()

        url = "https://serpapi.com/search.json"
        params = {
            "q": query,
            "location": location,
            "api_key": settings.serpapi_key,
            "engine": "google",
            "num": 10,
        }

        try:
            resp = self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            result = {
                "query": query,
                "related_searches": [
                    rs.get("query", "") for rs in data.get("related_searches", [])
                ],
                "related_questions": [
                    rq.get("question", "") for rq in data.get("related_questions", [])
                ],
                "organic_results_count": len(data.get("organic_results", [])),
                "search_information": data.get("search_information", {}),
            }
            self.cache.set(cache_key, result)
            return result
        except Exception as exc:
            logger.error("SerpAPI error: %s", exc)
            return {"error": str(exc)}

    # ── AI-Powered Keyword Expansion ─────────────────────────────────

    def ai_expand_keywords(
        self, seed: str, count: int = 20, provider_name: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Use AI to generate keyword ideas with estimated metrics.

        Returns:
            List of dicts: {keyword, intent, difficulty_estimate, notes}
        """
        from rankforge.ai.base import get_ai_provider

        provider = get_ai_provider(provider_name)

        prompt = (
            f"You are an SEO keyword research expert. For the seed keyword '{seed}', "
            f"generate {count} related keyword ideas. For each keyword provide:\n"
            f"- keyword: the keyword phrase\n"
            f"- search_intent: informational, navigational, commercial, or transactional\n"
            f"- difficulty: low, medium, or high (your estimate)\n"
            f"- monthly_volume_estimate: rough range like '100-500'\n"
            f"- notes: brief SEO tip\n\n"
            f"Return as valid JSON array. No markdown fences, just the JSON."
        )

        try:
            raw = provider.generate_content(prompt)
            # Extract JSON from response (handle markdown fences if present)
            json_match = re.search(r'\[.*\]', raw, re.DOTALL)
            if json_match:
                keywords = json.loads(json_match.group())
            else:
                keywords = json.loads(raw)
            return keywords
        except (json.JSONDecodeError, Exception) as exc:
            logger.error("AI keyword expansion failed: %s", exc)
            return [{"keyword": seed, "error": str(exc)}]

    # ── Combined Research ────────────────────────────────────────────

    def research(
        self,
        query: str,
        use_ai: bool = True,
        ai_provider: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Run a full keyword research pipeline combining all sources.

        Returns:
            Combined results dict with autocomplete, serpapi, and AI data.
        """
        Display.section(f"Keyword Research: '{query}'")

        results: dict[str, Any] = {"query": query, "sources": {}}

        # 1. Google Autocomplete
        with Display.spinner("Fetching Google Autocomplete...") as progress:
            progress.add_task("autocomplete", total=None)
            autocomplete = self.google_autocomplete(query)
            results["sources"]["autocomplete"] = autocomplete

        if autocomplete:
            Display.success(f"Google Autocomplete: {len(autocomplete)} suggestions")

        # 2. SerpAPI
        if settings.serpapi_key:
            with Display.spinner("Querying SerpAPI...") as progress:
                progress.add_task("serpapi", total=None)
                serpapi_data = self.serpapi_keywords(query)
                results["sources"]["serpapi"] = serpapi_data
            Display.success("SerpAPI data retrieved")
        else:
            Display.warning("SerpAPI key not configured -- skipping.")

        # 3. AI Expansion
        if use_ai:
            with Display.spinner("AI-powered keyword expansion...") as progress:
                progress.add_task("ai", total=None)
                ai_keywords = self.ai_expand_keywords(query, provider_name=ai_provider)
                results["sources"]["ai_expanded"] = ai_keywords
            Display.success(f"AI generated {len(ai_keywords)} keyword ideas")

        # ── Display Results ──────────────────────────────────────────
        if autocomplete:
            Display.table(
                "Google Autocomplete Suggestions",
                columns=[
                    {"name": "#", "style": "dim", "justify": "right"},
                    {"name": "Keyword Suggestion", "style": "green"},
                ],
                rows=[[str(i + 1), kw] for i, kw in enumerate(autocomplete[:15])],
            )

        if use_ai and isinstance(results["sources"].get("ai_expanded"), list):
            ai_rows = []
            for kw in results["sources"]["ai_expanded"][:15]:
                if isinstance(kw, dict) and "keyword" in kw:
                    ai_rows.append([
                        kw.get("keyword", ""),
                        kw.get("search_intent", ""),
                        kw.get("difficulty", ""),
                        kw.get("monthly_volume_estimate", ""),
                    ])
            if ai_rows:
                Display.table(
                    "AI-Expanded Keywords",
                    columns=[
                        {"name": "Keyword", "style": "cyan"},
                        {"name": "Intent", "style": "yellow"},
                        {"name": "Difficulty", "style": "magenta"},
                        {"name": "Est. Volume", "style": "green"},
                    ],
                    rows=ai_rows,
                )

        return results
