"""
RankForge CLI - SERP Analysis Module
=======================================
Scrape and analyse Search Engine Results Pages.
Uses SerpAPI when available, or direct scraping with BeautifulSoup as fallback.
"""

import re
from typing import Any, Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger
from rankforge.utils.cache import Cache
from rankforge.utils.rate_limiter import RateLimiter
from rankforge.utils.display import Display

logger = get_logger("rankforge.seo.serp")


class SerpAnalyzer:
    """
    SERP analysis engine.

    Retrieves and analyses the top search results for a given query,
    extracting titles, URLs, snippets, and SERP features.
    """

    def __init__(self):
        self.cache = Cache(namespace="serp")
        self.limiter = RateLimiter()

    # ── SerpAPI Backend ──────────────────────────────────────────────

    def _serp_via_api(self, query: str, num: int = 10, location: str = "United States") -> dict[str, Any]:
        """Fetch SERP data from SerpAPI."""
        cache_key = f"serpapi:serp:{location}:{query}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        self.limiter.acquire()

        params = {
            "q": query,
            "api_key": settings.serpapi_key,
            "engine": "google",
            "num": num,
            "location": location,
        }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get("https://serpapi.com/search.json", params=params)
                resp.raise_for_status()
                data = resp.json()

            # Extract organic results
            organic = []
            for item in data.get("organic_results", []):
                organic.append({
                    "position": item.get("position", 0),
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "displayed_link": item.get("displayed_link", ""),
                })

            # Extract SERP features
            features = []
            if data.get("knowledge_graph"):
                features.append("Knowledge Graph")
            if data.get("answer_box"):
                features.append("Answer Box")
            if data.get("local_results"):
                features.append("Local Pack")
            if data.get("shopping_results"):
                features.append("Shopping Results")
            if data.get("related_questions"):
                features.append("People Also Ask")
            if data.get("related_searches"):
                features.append("Related Searches")

            result = {
                "query": query,
                "total_results": data.get("search_information", {}).get("total_results", 0),
                "organic_results": organic,
                "serp_features": features,
                "related_searches": [
                    rs.get("query", "") for rs in data.get("related_searches", [])
                ],
                "people_also_ask": [
                    rq.get("question", "") for rq in data.get("related_questions", [])
                ],
            }
            self.cache.set(cache_key, result)
            return result

        except Exception as exc:
            logger.error("SerpAPI SERP error: %s", exc)
            return {"query": query, "error": str(exc)}

    # ── Direct Scraping Backend ──────────────────────────────────────

    def _serp_via_scraping(self, query: str, num: int = 10) -> dict[str, Any]:
        """
        Scrape Google search results directly using BeautifulSoup.
        Note: This is rate-limited and may be blocked. Use SerpAPI for production.
        """
        cache_key = f"scrape:serp:{query}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        self.limiter.acquire()

        url = f"https://www.google.com/search?q={quote_plus(query)}&num={num}&hl=en"
        headers = {
            "User-Agent": settings.scraper_user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            with httpx.Client(timeout=settings.scraper_timeout, follow_redirects=True) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            organic = []
            # Google's result containers (class names may change)
            for idx, div in enumerate(soup.select("div.g"), start=1):
                title_el = div.select_one("h3")
                link_el = div.select_one("a")
                snippet_el = div.select_one("div.VwiC3b") or div.select_one("span.aCOpRe")

                if title_el and link_el:
                    href = link_el.get("href", "")
                    if href.startswith("/url?q="):
                        href = href.split("/url?q=")[1].split("&")[0]
                    organic.append({
                        "position": idx,
                        "title": title_el.get_text(strip=True),
                        "url": href,
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })
                if len(organic) >= num:
                    break

            # Related searches
            related = []
            for a in soup.select("div#brs a"):
                related.append(a.get_text(strip=True))

            result = {
                "query": query,
                "organic_results": organic,
                "related_searches": related,
                "serp_features": [],
                "source": "direct_scrape",
                "note": "Scraped results may be incomplete. Use SerpAPI for full data.",
            }
            self.cache.set(cache_key, result)
            return result

        except Exception as exc:
            logger.error("SERP scraping error: %s", exc)
            return {"query": query, "error": str(exc)}

    # ── Combined Analysis ────────────────────────────────────────────

    def analyze(self, query: str, num_results: int = 10) -> dict[str, Any]:
        """
        Analyse SERP for a query using the best available method.

        Returns:
            Structured SERP analysis results.
        """
        Display.section(f"SERP Analysis: '{query}'")

        if settings.serpapi_key:
            Display.info("Using SerpAPI for SERP data...")
            with Display.spinner("Fetching SERP results...") as progress:
                progress.add_task("serp", total=None)
                results = self._serp_via_api(query, num=num_results)
        else:
            Display.warning("SerpAPI not configured -- using direct scraping (limited).")
            with Display.spinner("Scraping SERP results...") as progress:
                progress.add_task("scrape", total=None)
                results = self._serp_via_scraping(query, num=num_results)

        # ── Display Results ──────────────────────────────────────────
        if "error" not in results:
            organic = results.get("organic_results", [])
            if organic:
                rows = []
                for r in organic[:10]:
                    rows.append([
                        str(r.get("position", "")),
                        r.get("title", "")[:55],
                        r.get("url", "")[:50],
                        r.get("snippet", "")[:60],
                    ])
                Display.table(
                    f"Top {len(rows)} Organic Results",
                    columns=[
                        {"name": "#", "style": "dim", "justify": "right"},
                        {"name": "Title", "style": "cyan"},
                        {"name": "URL", "style": "green"},
                        {"name": "Snippet", "style": "dim"},
                    ],
                    rows=rows,
                )

            features = results.get("serp_features", [])
            if features:
                Display.key_value(
                    {"SERP Features": ", ".join(features)},
                    title="Feature Analysis",
                )

            paa = results.get("people_also_ask", [])
            if paa:
                Display.table(
                    "People Also Ask",
                    columns=[{"name": "Question", "style": "yellow"}],
                    rows=[[q] for q in paa[:8]],
                )
        else:
            Display.error(f"SERP analysis failed: {results['error']}")

        return results
