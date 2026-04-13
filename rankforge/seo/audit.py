"""
RankForge CLI - Site Audit Module
====================================
On-page SEO audit: checks meta tags, headings, images, links,
page speed indicators, mobile-friendliness, and more.
"""

import re
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger
from rankforge.utils.cache import Cache
from rankforge.utils.rate_limiter import RateLimiter
from rankforge.utils.display import Display

logger = get_logger("rankforge.seo.audit")


class SiteAuditor:
    """
    On-page SEO auditor.

    Fetches the target URL (or homepage) and evaluates against
    common SEO best practices, returning a structured report
    with scores and actionable recommendations.
    """

    def __init__(self):
        self.cache = Cache(namespace="audit")
        self.limiter = RateLimiter()

    # ── Fetch Page ───────────────────────────────────────────────────

    def _fetch(self, url: str) -> tuple[str, int, dict[str, str]]:
        """Fetch page HTML, returning (html, status_code, headers)."""
        self.limiter.acquire()

        headers = {"User-Agent": settings.scraper_user_agent}
        with httpx.Client(
            timeout=settings.scraper_timeout,
            follow_redirects=True,
            verify=False,
        ) as client:
            resp = client.get(url, headers=headers)
            return resp.text, resp.status_code, dict(resp.headers)

    # ── Individual Checks ────────────────────────────────────────────

    def _check_meta(self, soup: BeautifulSoup, url: str) -> dict[str, Any]:
        """Evaluate meta tags (title, description, viewport, canonical)."""
        issues = []
        score = 100

        # Title tag
        title_tag = soup.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else ""
        if not title_text:
            issues.append({"severity": "critical", "message": "Missing <title> tag"})
            score -= 25
        elif len(title_text) > 60:
            issues.append({"severity": "warning", "message": f"Title too long ({len(title_text)} chars, max 60)"})
            score -= 10
        elif len(title_text) < 20:
            issues.append({"severity": "warning", "message": f"Title too short ({len(title_text)} chars, min 20)"})
            score -= 5

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        desc_content = meta_desc.get("content", "") if meta_desc else ""
        if not desc_content:
            issues.append({"severity": "critical", "message": "Missing meta description"})
            score -= 20
        elif len(desc_content) > 160:
            issues.append({"severity": "warning", "message": f"Meta description too long ({len(desc_content)} chars)"})
            score -= 5
        elif len(desc_content) < 50:
            issues.append({"severity": "warning", "message": f"Meta description too short ({len(desc_content)} chars)"})
            score -= 5

        # Viewport
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if not viewport:
            issues.append({"severity": "warning", "message": "Missing viewport meta tag (mobile-friendliness)"})
            score -= 10

        # Canonical
        canonical = soup.find("link", attrs={"rel": "canonical"})
        canonical_href = canonical.get("href", "") if canonical else ""
        if not canonical_href:
            issues.append({"severity": "info", "message": "No canonical tag found"})
            score -= 3

        # Robots meta
        robots = soup.find("meta", attrs={"name": "robots"})
        robots_content = robots.get("content", "") if robots else ""

        return {
            "title": title_text,
            "title_length": len(title_text),
            "description": desc_content[:160],
            "description_length": len(desc_content),
            "has_viewport": bool(viewport),
            "canonical": canonical_href,
            "robots": robots_content,
            "issues": issues,
            "score": max(0, score),
        }

    def _check_headings(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Evaluate heading structure (H1-H6)."""
        issues = []
        score = 100
        heading_counts = {}

        for level in range(1, 7):
            tag = f"h{level}"
            elements = soup.find_all(tag)
            heading_counts[tag] = len(elements)

        # H1 checks
        h1_count = heading_counts.get("h1", 0)
        if h1_count == 0:
            issues.append({"severity": "critical", "message": "Missing H1 tag"})
            score -= 25
        elif h1_count > 1:
            issues.append({"severity": "warning", "message": f"Multiple H1 tags found ({h1_count})"})
            score -= 10

        # H2 checks
        if heading_counts.get("h2", 0) == 0:
            issues.append({"severity": "info", "message": "No H2 tags -- consider adding subheadings"})
            score -= 5

        h1_texts = [h.get_text(strip=True) for h in soup.find_all("h1")]

        return {
            "counts": heading_counts,
            "h1_texts": h1_texts,
            "issues": issues,
            "score": max(0, score),
        }

    def _check_images(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Check images for alt text and other attributes."""
        issues = []
        score = 100

        images = soup.find_all("img")
        total = len(images)
        missing_alt = 0
        missing_dimensions = 0

        for img in images:
            alt = img.get("alt", "")
            if not alt or not alt.strip():
                missing_alt += 1
            if not img.get("width") and not img.get("height"):
                missing_dimensions += 1

        if missing_alt > 0:
            pct = (missing_alt / total * 100) if total else 0
            severity = "critical" if pct > 50 else "warning"
            issues.append({"severity": severity, "message": f"{missing_alt}/{total} images missing alt text ({pct:.0f}%)"})
            score -= min(30, int(pct / 2))

        if missing_dimensions > total * 0.5 and total > 3:
            issues.append({"severity": "info", "message": "Many images lack explicit dimensions (CLS risk)"})
            score -= 5

        return {
            "total_images": total,
            "missing_alt": missing_alt,
            "missing_dimensions": missing_dimensions,
            "issues": issues,
            "score": max(0, score),
        }

    def _check_links(self, soup: BeautifulSoup, base_url: str) -> dict[str, Any]:
        """Analyse internal and external links."""
        issues = []
        score = 100
        parsed_base = urlparse(base_url)

        links = soup.find_all("a", href=True)
        internal = 0
        external = 0
        nofollow = 0
        broken_patterns = 0

        for a in links:
            href = a.get("href", "")
            rel = a.get("rel", [])

            if isinstance(rel, list) and "nofollow" in rel:
                nofollow += 1

            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            if parsed.netloc == parsed_base.netloc or not parsed.netloc:
                internal += 1
            else:
                external += 1

            # Flag suspicious link patterns
            if href in ("#", "javascript:void(0)", "javascript:;"):
                broken_patterns += 1

        if broken_patterns > 0:
            issues.append({"severity": "warning", "message": f"{broken_patterns} links with placeholder/empty hrefs"})
            score -= min(15, broken_patterns * 3)

        if internal == 0:
            issues.append({"severity": "info", "message": "No internal links detected"})
            score -= 10

        return {
            "total_links": len(links),
            "internal": internal,
            "external": external,
            "nofollow": nofollow,
            "broken_patterns": broken_patterns,
            "issues": issues,
            "score": max(0, score),
        }

    def _check_performance_hints(self, html: str, headers: dict[str, str]) -> dict[str, Any]:
        """Basic performance indicators from HTML and headers."""
        issues = []
        score = 100

        # Page size
        size_kb = len(html.encode("utf-8")) / 1024
        if size_kb > 500:
            issues.append({"severity": "warning", "message": f"Large HTML size ({size_kb:.0f} KB)"})
            score -= 10

        # Compression
        content_encoding = headers.get("content-encoding", "")
        if "gzip" not in content_encoding and "br" not in content_encoding:
            issues.append({"severity": "info", "message": "No gzip/brotli compression detected"})
            score -= 5

        # Inline styles
        soup = BeautifulSoup(html, "html.parser")
        inline_styles = soup.find_all(style=True)
        if len(inline_styles) > 20:
            issues.append({"severity": "info", "message": f"{len(inline_styles)} elements with inline styles"})
            score -= 3

        # External scripts
        scripts = soup.find_all("script", src=True)
        if len(scripts) > 15:
            issues.append({"severity": "warning", "message": f"{len(scripts)} external scripts -- may impact load time"})
            score -= 5

        return {
            "html_size_kb": round(size_kb, 1),
            "compression": content_encoding or "none",
            "external_scripts": len(scripts),
            "inline_styles": len(inline_styles),
            "issues": issues,
            "score": max(0, score),
        }

    # ── Full Audit ───────────────────────────────────────────────────

    def audit(self, domain: str) -> dict[str, Any]:
        """
        Run a comprehensive on-page SEO audit.

        Args:
            domain: Domain or full URL to audit.

        Returns:
            Structured audit report with per-category scores.
        """
        # Normalise URL
        url = domain if domain.startswith("http") else f"https://{domain}"

        Display.section(f"Site Audit: {url}")

        try:
            with Display.spinner("Fetching page...") as progress:
                progress.add_task("fetch", total=None)
                html, status_code, headers = self._fetch(url)
        except Exception as exc:
            Display.error(f"Failed to fetch {url}: {exc}")
            return {"url": url, "error": str(exc)}

        soup = BeautifulSoup(html, "html.parser")

        # Run all checks
        with Display.spinner("Running SEO checks...") as progress:
            progress.add_task("checks", total=None)
            meta = self._check_meta(soup, url)
            headings = self._check_headings(soup)
            images = self._check_images(soup)
            links = self._check_links(soup, url)
            performance = self._check_performance_hints(html, headers)

        # Calculate overall score
        scores = [meta["score"], headings["score"], images["score"], links["score"], performance["score"]]
        overall_score = int(sum(scores) / len(scores))

        report = {
            "url": url,
            "status_code": status_code,
            "overall_score": overall_score,
            "categories": {
                "meta_tags": meta,
                "headings": headings,
                "images": images,
                "links": links,
                "performance": performance,
            },
        }

        # ── Display Report ───────────────────────────────────────────
        # Score color
        if overall_score >= 80:
            score_color = "green"
        elif overall_score >= 60:
            score_color = "yellow"
        else:
            score_color = "red"

        Display.key_value(
            {
                "URL": url,
                "Status Code": str(status_code),
                "Overall Score": f"[bold {score_color}]{overall_score}/100[/]",
            },
            title="Audit Summary",
        )

        # Category scores table
        Display.table(
            "Category Scores",
            columns=[
                {"name": "Category", "style": "cyan"},
                {"name": "Score", "justify": "right"},
                {"name": "Issues", "justify": "right"},
            ],
            rows=[
                ["Meta Tags", f"{meta['score']}/100", str(len(meta['issues']))],
                ["Headings", f"{headings['score']}/100", str(len(headings['issues']))],
                ["Images", f"{images['score']}/100", str(len(images['issues']))],
                ["Links", f"{links['score']}/100", str(len(links['issues']))],
                ["Performance", f"{performance['score']}/100", str(len(performance['issues']))],
            ],
        )

        # All issues
        all_issues = []
        for cat_name, cat_data in report["categories"].items():
            for issue in cat_data.get("issues", []):
                all_issues.append({**issue, "category": cat_name})

        if all_issues:
            issue_rows = []
            for issue in sorted(all_issues, key=lambda x: {"critical": 0, "warning": 1, "info": 2}.get(x["severity"], 3)):
                sev = issue["severity"]
                if sev == "critical":
                    sev_display = "[bold red]CRITICAL[/]"
                elif sev == "warning":
                    sev_display = "[yellow]WARNING[/]"
                else:
                    sev_display = "[dim]INFO[/]"
                issue_rows.append([
                    sev_display,
                    issue["category"].replace("_", " ").title(),
                    issue["message"],
                ])

            Display.table(
                "Issues Found",
                columns=[
                    {"name": "Severity"},
                    {"name": "Category", "style": "cyan"},
                    {"name": "Issue", "style": "white"},
                ],
                rows=issue_rows,
            )

        return report
