"""
RankForge CLI - Backlink Analysis Module
==========================================
Analyse backlink profiles using DataForSEO or simulated data.
Provides domain authority estimates, referring domains, and anchor text distribution.
"""

import json
import base64
from typing import Any, Optional

import httpx

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger
from rankforge.utils.cache import Cache
from rankforge.utils.rate_limiter import RateLimiter
from rankforge.utils.display import Display

logger = get_logger("rankforge.seo.backlinks")


class BacklinkAnalyzer:
    """
    Backlink analysis engine.

    Uses DataForSEO API when credentials are available,
    otherwise provides a simulated analysis with AI-generated insights.
    """

    def __init__(self):
        self.cache = Cache(namespace="backlinks")
        self.limiter = RateLimiter()
        self.has_dataforseo = bool(
            settings.dataforseo_login and settings.dataforseo_password
        )

    # ── DataForSEO Integration ───────────────────────────────────────

    def _dataforseo_headers(self) -> dict[str, str]:
        """Build DataForSEO auth headers."""
        creds = f"{settings.dataforseo_login}:{settings.dataforseo_password}"
        token = base64.b64encode(creds.encode()).decode()
        return {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

    def dataforseo_backlinks(self, domain: str, limit: int = 50) -> dict[str, Any]:
        """
        Fetch backlink data from DataForSEO's Backlinks API.

        Returns:
            Dict with summary metrics and top backlinks.
        """
        cache_key = f"dataforseo:backlinks:{domain}:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        self.limiter.acquire()

        url = "https://api.dataforseo.com/v3/backlinks/backlinks/live"
        payload = [
            {
                "target": domain,
                "limit": limit,
                "order_by": ["rank,desc"],
                "filters": ["dofollow", "=", True],
            }
        ]

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    url, headers=self._dataforseo_headers(), json=payload
                )
                resp.raise_for_status()
                data = resp.json()

            tasks = data.get("tasks", [])
            if tasks and tasks[0].get("result"):
                result = tasks[0]["result"][0]
                backlinks = []
                for bl in result.get("items", []):
                    backlinks.append({
                        "source_url": bl.get("url_from", ""),
                        "target_url": bl.get("url_to", ""),
                        "anchor": bl.get("anchor", ""),
                        "rank": bl.get("rank", 0),
                        "is_dofollow": bl.get("dofollow", False),
                        "first_seen": bl.get("first_seen", ""),
                    })

                output = {
                    "domain": domain,
                    "total_backlinks": result.get("total_count", 0),
                    "backlinks": backlinks,
                }
                self.cache.set(cache_key, output)
                return output

            return {"domain": domain, "error": "No results from DataForSEO"}

        except Exception as exc:
            logger.error("DataForSEO backlinks error: %s", exc)
            return {"domain": domain, "error": str(exc)}

    # ── DataForSEO Summary ───────────────────────────────────────────

    def dataforseo_summary(self, domain: str) -> dict[str, Any]:
        """Fetch high-level backlink summary from DataForSEO."""
        cache_key = f"dataforseo:summary:{domain}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        self.limiter.acquire()

        url = "https://api.dataforseo.com/v3/backlinks/summary/live"
        payload = [{"target": domain}]

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    url, headers=self._dataforseo_headers(), json=payload
                )
                resp.raise_for_status()
                data = resp.json()

            tasks = data.get("tasks", [])
            if tasks and tasks[0].get("result"):
                result = tasks[0]["result"][0]
                summary = {
                    "domain": domain,
                    "total_backlinks": result.get("total_backlinks", 0),
                    "referring_domains": result.get("referring_domains", 0),
                    "referring_ips": result.get("referring_ips", 0),
                    "dofollow": result.get("referring_links_types", {}).get("dofollow", 0),
                    "nofollow": result.get("referring_links_types", {}).get("nofollow", 0),
                    "rank": result.get("rank", 0),
                }
                self.cache.set(cache_key, summary)
                return summary

            return {"domain": domain, "error": "No summary data"}

        except Exception as exc:
            logger.error("DataForSEO summary error: %s", exc)
            return {"domain": domain, "error": str(exc)}

    # ── Simulated Backlink Analysis ──────────────────────────────────

    def simulated_analysis(self, domain: str) -> dict[str, Any]:
        """
        Provide a simulated backlink analysis with AI-generated insights
        when no API credentials are configured.
        """
        from rankforge.ai.base import get_ai_provider

        try:
            provider = get_ai_provider()
            prompt = (
                f"As an SEO expert, provide a realistic backlink profile analysis for "
                f"the domain '{domain}'. Include:\n"
                f"1. Estimated domain authority (0-100)\n"
                f"2. Estimated total backlinks range\n"
                f"3. Estimated referring domains range\n"
                f"4. Likely anchor text distribution (branded, generic, keyword-rich)\n"
                f"5. Top 5 likely referring domains (realistic examples)\n"
                f"6. Backlink quality assessment\n"
                f"7. Recommendations for improvement\n\n"
                f"Format as structured text with clear sections."
            )
            analysis = provider.generate_content(prompt)
            return {
                "domain": domain,
                "type": "ai_simulated",
                "analysis": analysis,
                "note": "This is an AI-estimated analysis. Use DataForSEO API for real data.",
            }
        except Exception as exc:
            logger.error("Simulated analysis failed: %s", exc)
            return {"domain": domain, "error": str(exc)}

    # ── Combined Analysis ────────────────────────────────────────────

    def analyze(self, domain: str) -> dict[str, Any]:
        """
        Run full backlink analysis using best available source.

        Returns:
            Structured backlink analysis results.
        """
        Display.section(f"Backlink Analysis: {domain}")

        if self.has_dataforseo:
            Display.info("Using DataForSEO API for backlink data...")

            with Display.spinner("Fetching backlink summary...") as progress:
                progress.add_task("summary", total=None)
                summary = self.dataforseo_summary(domain)

            with Display.spinner("Fetching top backlinks...") as progress:
                progress.add_task("backlinks", total=None)
                backlinks = self.dataforseo_backlinks(domain)

            results = {**summary, "top_backlinks": backlinks.get("backlinks", [])}

            # Display summary
            if "error" not in summary:
                Display.key_value(
                    {
                        "Domain": domain,
                        "Total Backlinks": f"{summary.get('total_backlinks', 'N/A'):,}",
                        "Referring Domains": f"{summary.get('referring_domains', 'N/A'):,}",
                        "Dofollow": f"{summary.get('dofollow', 'N/A'):,}",
                        "Nofollow": f"{summary.get('nofollow', 'N/A'):,}",
                        "Domain Rank": summary.get("rank", "N/A"),
                    },
                    title="Backlink Summary",
                )

            # Display top backlinks table
            bl_rows = []
            for bl in backlinks.get("backlinks", [])[:10]:
                bl_rows.append([
                    bl.get("source_url", "")[:50],
                    bl.get("anchor", "-")[:30],
                    str(bl.get("rank", 0)),
                    "Yes" if bl.get("is_dofollow") else "No",
                ])
            if bl_rows:
                Display.table(
                    "Top Backlinks",
                    columns=[
                        {"name": "Source URL", "style": "cyan"},
                        {"name": "Anchor Text", "style": "green"},
                        {"name": "Rank", "justify": "right"},
                        {"name": "Dofollow"},
                    ],
                    rows=bl_rows,
                )

            return results
        else:
            Display.warning("DataForSEO not configured -- using AI-simulated analysis.")
            with Display.spinner("Generating AI backlink analysis...") as progress:
                progress.add_task("ai", total=None)
                result = self.simulated_analysis(domain)

            if "analysis" in result:
                Display.markdown(result["analysis"])

            return result
