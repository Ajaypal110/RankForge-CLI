"""
RankForge CLI - Competitor Analysis Module
=============================================
Analyse competitors' SEO strategies: their top pages, keyword gaps,
backlink comparison, and content strategies.
"""

import json
import re
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger
from rankforge.utils.cache import Cache
from rankforge.utils.rate_limiter import RateLimiter
from rankforge.utils.display import Display

logger = get_logger("rankforge.seo.competitors")


class CompetitorAnalyzer:
    """
    Competitor SEO analysis engine.

    Combines scraping and AI-powered analysis to profile competitors.
    """

    def __init__(self):
        self.cache = Cache(namespace="competitors")
        self.limiter = RateLimiter()
        self.client = httpx.Client(
            headers={"User-Agent": settings.scraper_user_agent},
            timeout=settings.scraper_timeout,
            follow_redirects=True,
        )

    # ── Find Competitors via SERP ────────────────────────────────────

    def find_competitors(self, domain: str, niche_keywords: Optional[list[str]] = None) -> list[dict[str, Any]]:
        """
        Discover competitors from SERP by searching for domain-related keywords.

        Args:
            domain: Your domain.
            niche_keywords: Optional list of niche keywords to search for.

        Returns:
            List of competitor dicts with domain, frequency, and overlap info.
        """
        if not niche_keywords:
            # Auto-generate keywords from domain name
            parsed = urlparse(domain if "://" in domain else f"https://{domain}")
            domain_name = parsed.netloc or parsed.path
            parts = domain_name.replace("www.", "").split(".")[0]
            niche_keywords = [parts, f"{parts} services", f"best {parts}"]

        competitor_count: dict[str, int] = {}
        competitor_urls: dict[str, list[str]] = {}

        from rankforge.seo.serp import SerpAnalyzer
        serp = SerpAnalyzer()

        for kw in niche_keywords:
            results = serp.analyze(kw)
            for item in results.get("organic_results", []):
                comp_domain = urlparse(item.get("url", "")).netloc
                if comp_domain and comp_domain not in domain:
                    competitor_count[comp_domain] = competitor_count.get(comp_domain, 0) + 1
                    if comp_domain not in competitor_urls:
                        competitor_urls[comp_domain] = []
                    competitor_urls[comp_domain].append(item.get("url", ""))

        # Sort by frequency (most overlapping = strongest competitor)
        competitors = []
        for comp_domain, count in sorted(competitor_count.items(), key=lambda x: x[1], reverse=True)[:15]:
            competitors.append({
                "domain": comp_domain,
                "overlap_score": count,
                "keywords_overlap": count,
                "sample_urls": competitor_urls.get(comp_domain, [])[:3],
            })

        return competitors

    # ── Scrape Competitor Meta Info ───────────────────────────────────

    def scrape_competitor_meta(self, domain: str) -> dict[str, Any]:
        """Scrape basic meta information from a competitor's homepage."""
        url = domain if domain.startswith("http") else f"https://{domain}"
        cache_key = f"comp_meta:{url}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        self.limiter.acquire()

        try:
            resp = self.client.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.find("title")
            desc = soup.find("meta", attrs={"name": "description"})
            h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]

            # Count content elements
            word_count = len(soup.get_text().split())
            internal_links = len([a for a in soup.find_all("a", href=True) if urlparse(a["href"]).netloc in ("", urlparse(url).netloc)])
            external_links = len(soup.find_all("a", href=True)) - internal_links

            result = {
                "domain": domain,
                "url": url,
                "title": title.get_text(strip=True) if title else "",
                "description": desc.get("content", "") if desc else "",
                "h1_tags": h1s,
                "word_count": word_count,
                "internal_links": internal_links,
                "external_links": external_links,
                "has_schema": bool(soup.find("script", type="application/ld+json")),
                "has_og_tags": bool(soup.find("meta", property="og:title")),
            }
            self.cache.set(cache_key, result)
            return result

        except Exception as exc:
            logger.error("Failed to scrape %s: %s", domain, exc)
            return {"domain": domain, "error": str(exc)}

    # ── AI-Powered Competitor Insights ───────────────────────────────

    def ai_competitor_analysis(
        self,
        your_domain: str,
        competitor_domains: list[str],
        provider_name: Optional[str] = None,
    ) -> str:
        """
        Use AI to generate strategic competitor analysis insights.

        Returns:
            Markdown-formatted competitive analysis report.
        """
        from rankforge.ai.base import get_ai_provider

        provider = get_ai_provider(provider_name)

        # Gather meta info for all competitors
        competitor_info = []
        for domain in competitor_domains[:5]:
            meta = self.scrape_competitor_meta(domain)
            competitor_info.append(meta)

        prompt = (
            f"You are an SEO strategist. Analyse the competitive landscape for '{your_domain}'.\n\n"
            f"Competitor data:\n{json.dumps(competitor_info, indent=2, default=str)}\n\n"
            f"Provide:\n"
            f"1. **Competitive Overview**: How each competitor positions themselves\n"
            f"2. **Content Gap Analysis**: Topics/keywords competitors cover that '{your_domain}' might miss\n"
            f"3. **Strengths & Weaknesses**: For each competitor vs {your_domain}\n"
            f"4. **Opportunity Matrix**: Quick wins and long-term strategies\n"
            f"5. **Actionable Recommendations**: Top 5 things to do now\n\n"
            f"Format as markdown with clear sections."
        )

        return provider.generate_content(prompt, max_tokens=3000)

    # ── Combined Analysis ────────────────────────────────────────────

    def analyze(
        self,
        domain: str,
        niche_keywords: Optional[list[str]] = None,
        use_ai: bool = True,
        ai_provider: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Run a full competitor analysis pipeline.

        Returns:
            Comprehensive competitor analysis results.
        """
        Display.section(f"Competitor Analysis: {domain}")

        # 1. Find competitors
        Display.info("Discovering competitors from SERP...")
        with Display.spinner("Scanning search results...") as progress:
            progress.add_task("find", total=None)
            competitors = self.find_competitors(domain, niche_keywords)

        if competitors:
            Display.table(
                "Top Competitors",
                columns=[
                    {"name": "#", "style": "dim", "justify": "right"},
                    {"name": "Domain", "style": "cyan"},
                    {"name": "Overlap Score", "justify": "right", "style": "green"},
                ],
                rows=[
                    [str(i + 1), c["domain"], str(c["overlap_score"])]
                    for i, c in enumerate(competitors[:10])
                ],
            )
        else:
            Display.warning("No competitors found. Try providing niche keywords.")

        # 2. Scrape competitor meta
        comp_domains = [c["domain"] for c in competitors[:5]]
        meta_data = []
        if comp_domains:
            with Display.spinner("Gathering competitor intelligence...") as progress:
                progress.add_task("meta", total=None)
                for cd in comp_domains:
                    meta = self.scrape_competitor_meta(cd)
                    meta_data.append(meta)

            meta_rows = []
            for m in meta_data:
                if "error" not in m:
                    meta_rows.append([
                        m.get("domain", ""),
                        m.get("title", "")[:40],
                        str(m.get("word_count", 0)),
                        "Yes" if m.get("has_schema") else "No",
                        "Yes" if m.get("has_og_tags") else "No",
                    ])
            if meta_rows:
                Display.table(
                    "Competitor Homepage Analysis",
                    columns=[
                        {"name": "Domain", "style": "cyan"},
                        {"name": "Title", "style": "green"},
                        {"name": "Words", "justify": "right"},
                        {"name": "Schema"},
                        {"name": "OG Tags"},
                    ],
                    rows=meta_rows,
                )

        # 3. AI insights
        ai_insights = ""
        if use_ai and comp_domains:
            with Display.spinner("Generating AI competitive insights...") as progress:
                progress.add_task("ai", total=None)
                ai_insights = self.ai_competitor_analysis(domain, comp_domains, ai_provider)
            Display.section("AI Competitive Analysis")
            Display.markdown(ai_insights)

        return {
            "domain": domain,
            "competitors": competitors,
            "competitor_meta": meta_data,
            "ai_insights": ai_insights,
        }
