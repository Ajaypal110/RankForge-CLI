"""
RankForge CLI - Guest Post & Link Opportunity Scraper
=======================================================
Find guest post opportunities, resource pages, and link-building targets
using Google search footprints and scraping.
"""

import re
from typing import Any, Optional
from urllib.parse import urljoin, urlparse, quote_plus

import httpx
from bs4 import BeautifulSoup

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger
from rankforge.utils.cache import Cache
from rankforge.utils.rate_limiter import RateLimiter
from rankforge.utils.display import Display

logger = get_logger("rankforge.automation.scraper")

# ── Google Search Footprints for Link Building ───────────────────────
GUEST_POST_FOOTPRINTS = [
    '"{niche}" + "write for us"',
    '"{niche}" + "guest post"',
    '"{niche}" + "guest article"',
    '"{niche}" + "contribute"',
    '"{niche}" + "submit a post"',
    '"{niche}" + "become a contributor"',
    '"{niche}" + "accepting guest posts"',
    '"{niche}" + "guest author"',
    '"{niche}" + "submit an article"',
    '"{niche}" + "blogger wanted"',
]

RESOURCE_PAGE_FOOTPRINTS = [
    '"{niche}" + "resources" + inurl:resources',
    '"{niche}" + "useful links"',
    '"{niche}" + "recommended sites"',
    '"{niche}" + "helpful resources"',
]

# ── Email Extraction Patterns ────────────────────────────────────────
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)


class GuestPostFinder:
    """
    Discover guest posting opportunities and link-building targets.

    Uses Google search footprints to find relevant sites,
    then scrapes them for contact information.
    """

    def __init__(self):
        self.cache = Cache(namespace="guest_posts")
        self.limiter = RateLimiter()
        self.client = httpx.Client(
            headers={"User-Agent": settings.scraper_user_agent},
            timeout=settings.scraper_timeout,
            follow_redirects=True,
        )

    # ── Search for Opportunities ─────────────────────────────────────

    def search_footprint(self, query: str, num_results: int = 10) -> list[dict[str, str]]:
        """
        Search Google with a specific footprint query.

        Returns:
            List of dicts with title, url, snippet.
        """
        cache_key = f"footprint:{query}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        self.limiter.acquire()

        url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"
        headers = {
            "User-Agent": settings.scraper_user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        }

        results = []
        try:
            resp = self.client.get(url, headers=headers)
            soup = BeautifulSoup(resp.text, "html.parser")

            for div in soup.select("div.g"):
                title_el = div.select_one("h3")
                link_el = div.select_one("a")
                snippet_el = div.select_one("div.VwiC3b")

                if title_el and link_el:
                    href = link_el.get("href", "")
                    if href.startswith("/url?q="):
                        href = href.split("/url?q=")[1].split("&")[0]

                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": href,
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })

            self.cache.set(cache_key, results)
            return results

        except Exception as exc:
            logger.error("Footprint search error: %s", exc)
            return []

    def find_guest_post_sites(self, niche: str, max_results: int = 30) -> list[dict[str, Any]]:
        """
        Find guest post opportunities for a given niche.

        Args:
            niche: The niche/topic to search for.
            max_results: Maximum total results to collect.

        Returns:
            Deduplicated list of guest post opportunities.
        """
        Display.section(f"Finding Guest Post Opportunities: '{niche}'")

        all_results = []
        seen_domains = set()

        for footprint_template in GUEST_POST_FOOTPRINTS:
            if len(all_results) >= max_results:
                break

            footprint = footprint_template.format(niche=niche)
            with Display.spinner(f"Searching: {footprint[:60]}...") as progress:
                progress.add_task("search", total=None)
                results = self.search_footprint(footprint)

            for r in results:
                domain = urlparse(r["url"]).netloc
                if domain not in seen_domains:
                    seen_domains.add(domain)
                    all_results.append({**r, "domain": domain, "footprint": footprint})

        # Display results
        if all_results:
            rows = []
            for i, r in enumerate(all_results[:20], 1):
                rows.append([
                    str(i),
                    r.get("domain", "")[:35],
                    r.get("title", "")[:45],
                ])
            Display.table(
                f"Guest Post Opportunities ({len(all_results)} found)",
                columns=[
                    {"name": "#", "style": "dim", "justify": "right"},
                    {"name": "Domain", "style": "cyan"},
                    {"name": "Title", "style": "green"},
                ],
                rows=rows,
            )
        else:
            Display.warning("No guest post opportunities found.")

        return all_results

    # ── Extract Contact Information ──────────────────────────────────

    def extract_emails(self, url: str) -> list[str]:
        """
        Extract email addresses from a webpage.

        Checks the main page and common contact page paths.
        """
        emails = set()

        # Pages to check
        pages_to_check = [url]
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        for path in ["/contact", "/contact-us", "/about", "/write-for-us", "/contribute"]:
            pages_to_check.append(urljoin(base, path))

        for page_url in pages_to_check:
            self.limiter.acquire()
            try:
                resp = self.client.get(page_url)
                if resp.status_code == 200:
                    found = EMAIL_REGEX.findall(resp.text)
                    # Filter out common false positives
                    for email in found:
                        if not any(x in email.lower() for x in ["@example", "@test", "@sentry", ".png", ".jpg", "@2x"]):
                            emails.add(email.lower())
            except Exception:
                continue

        return sorted(emails)

    def extract_contact_pages(self, url: str) -> list[str]:
        """Find contact-related pages on a website."""
        self.limiter.acquire()
        contact_pages = []

        try:
            resp = self.client.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")

            contact_keywords = ["contact", "about", "write for us", "contribute", "submit", "guest"]
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True).lower()
                href = a.get("href", "").lower()
                if any(kw in text or kw in href for kw in contact_keywords):
                    full_url = urljoin(url, a["href"])
                    if full_url not in contact_pages:
                        contact_pages.append(full_url)

        except Exception as exc:
            logger.error("Contact page extraction error: %s", exc)

        return contact_pages

    # ── Enrich Opportunities ─────────────────────────────────────────

    def enrich_opportunities(self, opportunities: list[dict[str, Any]], max_enrich: int = 10) -> list[dict[str, Any]]:
        """
        Enrich guest post opportunities with contact info.

        Args:
            opportunities: List from find_guest_post_sites().
            max_enrich: Max number of sites to enrich (rate limit friendly).

        Returns:
            Enriched opportunities with emails and contact pages.
        """
        Display.section("Enriching Opportunities with Contact Info")

        enriched = []
        for i, opp in enumerate(opportunities[:max_enrich]):
            with Display.spinner(f"[{i+1}/{min(max_enrich, len(opportunities))}] Extracting from {opp['domain']}...") as progress:
                progress.add_task("extract", total=None)
                emails = self.extract_emails(opp["url"])
                contact_pages = self.extract_contact_pages(opp["url"])

            opp["emails"] = emails
            opp["contact_pages"] = contact_pages
            enriched.append(opp)

            if emails:
                Display.success(f"{opp['domain']}: found {len(emails)} email(s)")
            else:
                Display.info(f"{opp['domain']}: no emails found, {len(contact_pages)} contact page(s)")

        return enriched
