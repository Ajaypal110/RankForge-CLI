"""
RankForge CLI - Submission Manager
=====================================
Simulated form submission and directory listing manager.
Logs all actions transparently — no hidden or deceptive automation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger
from rankforge.utils.display import Display
from rankforge.utils.export import Exporter
from rankforge.database.memory import ProjectMemory

logger = get_logger("rankforge.automation.submission")


# ── Common Free Directory / Listing Sites ────────────────────────────
DIRECTORY_SITES = [
    {"name": "Google Business Profile", "url": "https://business.google.com", "type": "local", "da_estimate": 100},
    {"name": "Bing Places", "url": "https://www.bingplaces.com", "type": "local", "da_estimate": 95},
    {"name": "Yelp", "url": "https://biz.yelp.com", "type": "local", "da_estimate": 94},
    {"name": "Apple Maps (Maps Connect)", "url": "https://mapsconnect.apple.com", "type": "local", "da_estimate": 100},
    {"name": "Facebook Business", "url": "https://www.facebook.com/business", "type": "social", "da_estimate": 96},
    {"name": "LinkedIn Company Page", "url": "https://www.linkedin.com/company/setup", "type": "social", "da_estimate": 98},
    {"name": "Crunchbase", "url": "https://www.crunchbase.com", "type": "business", "da_estimate": 91},
    {"name": "BBB", "url": "https://www.bbb.org", "type": "business", "da_estimate": 93},
    {"name": "Moz Local", "url": "https://moz.com/products/local", "type": "seo", "da_estimate": 91},
    {"name": "Hotfrog", "url": "https://www.hotfrog.com", "type": "directory", "da_estimate": 58},
    {"name": "Yellow Pages", "url": "https://www.yellowpages.com", "type": "directory", "da_estimate": 88},
    {"name": "DMOZ / Curlie", "url": "https://curlie.org", "type": "directory", "da_estimate": 82},
    {"name": "About.me", "url": "https://about.me", "type": "profile", "da_estimate": 85},
    {"name": "Gravatar", "url": "https://gravatar.com", "type": "profile", "da_estimate": 90},
    {"name": "Medium", "url": "https://medium.com", "type": "content", "da_estimate": 96},
    {"name": "Dev.to", "url": "https://dev.to", "type": "content", "da_estimate": 85},
    {"name": "Quora", "url": "https://www.quora.com", "type": "qa", "da_estimate": 93},
    {"name": "Reddit", "url": "https://www.reddit.com", "type": "social", "da_estimate": 97},
    {"name": "Pinterest", "url": "https://www.pinterest.com", "type": "social", "da_estimate": 94},
    {"name": "SlideShare", "url": "https://www.slideshare.net", "type": "content", "da_estimate": 95},
]


class SubmissionManager:
    """
    Directory submission planner and tracker.

    This module does NOT auto-fill or auto-submit forms.
    It generates a submission plan, tracks progress, and provides
    the URLs and information needed for manual submission.
    """

    def __init__(self, project_name: str = "default"):
        self.memory = ProjectMemory(project_name)
        self.exporter = Exporter("submissions")

    # ── Generate Submission Plan ─────────────────────────────────────

    def generate_plan(
        self,
        domain: str,
        business_name: str = "",
        business_type: str = "general",
        include_types: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """
        Generate a directory submission plan for a domain.

        Args:
            domain: Your domain.
            business_name: Your business name.
            business_type: Filter by type: local, social, business, directory, content, qa, profile.
            include_types: Specific types to include (None = all).

        Returns:
            List of submission tasks with URLs and status.
        """
        Display.section(f"Directory Submission Plan: {domain}")

        plan = []
        for site in DIRECTORY_SITES:
            if include_types and site["type"] not in include_types:
                continue

            plan.append({
                "directory_name": site["name"],
                "directory_url": site["url"],
                "type": site["type"],
                "da_estimate": site["da_estimate"],
                "domain": domain,
                "business_name": business_name or domain,
                "status": "pending",
                "submitted_at": None,
                "notes": "",
            })

        # Sort by DA (highest first)
        plan.sort(key=lambda x: x["da_estimate"], reverse=True)

        # Display
        rows = []
        for i, task in enumerate(plan, 1):
            rows.append([
                str(i),
                task["directory_name"],
                task["type"].upper(),
                str(task["da_estimate"]),
                task["directory_url"][:40],
                "Pending",
            ])

        Display.table(
            f"Submission Plan ({len(plan)} directories)",
            columns=[
                {"name": "#", "style": "dim", "justify": "right"},
                {"name": "Directory", "style": "cyan"},
                {"name": "Type", "style": "yellow"},
                {"name": "DA", "justify": "right", "style": "green"},
                {"name": "URL"},
                {"name": "Status"},
            ],
            rows=rows,
        )

        # Save plan
        self.memory.store("submissions", domain, plan)
        Display.success(f"Plan saved to project memory for '{domain}'")

        return plan

    # ── Track Submission Progress ────────────────────────────────────

    def update_status(
        self,
        domain: str,
        directory_name: str,
        status: str = "submitted",
        notes: str = "",
    ) -> bool:
        """
        Update the status of a directory submission.

        Args:
            domain: The domain the plan is for.
            directory_name: Name of the directory to update.
            status: New status (pending, submitted, approved, rejected).
            notes: Optional notes.

        Returns:
            True if updated successfully.
        """
        plan = self.memory.retrieve("submissions", domain)
        if not plan:
            Display.error(f"No submission plan found for '{domain}'")
            return False

        for task in plan:
            if task["directory_name"].lower() == directory_name.lower():
                task["status"] = status
                task["notes"] = notes
                if status == "submitted":
                    task["submitted_at"] = datetime.now().isoformat()
                self.memory.store("submissions", domain, plan)
                Display.success(f"Updated '{directory_name}' -> {status}")
                return True

        Display.error(f"Directory '{directory_name}' not found in plan.")
        return False

    # ── View Progress ────────────────────────────────────────────────

    def view_progress(self, domain: str) -> Optional[list[dict[str, Any]]]:
        """Display current submission progress for a domain."""
        plan = self.memory.retrieve("submissions", domain)
        if not plan:
            Display.warning(f"No submission plan found for '{domain}'. Run 'generate_plan' first.")
            return None

        # Calculate stats
        total = len(plan)
        submitted = sum(1 for t in plan if t["status"] == "submitted")
        approved = sum(1 for t in plan if t["status"] == "approved")
        pending = sum(1 for t in plan if t["status"] == "pending")

        Display.section(f"Submission Progress: {domain}")
        Display.key_value(
            {
                "Total Directories": str(total),
                "Submitted": f"[yellow]{submitted}[/]",
                "Approved": f"[green]{approved}[/]",
                "Pending": f"[dim]{pending}[/]",
                "Completion": f"{((submitted + approved) / total * 100):.0f}%",
            },
            title="Progress Summary",
        )

        # Status table
        rows = []
        status_icons = {"pending": "[ ]", "submitted": "[>]", "approved": "[Y]", "rejected": "[N]"}
        for task in plan:
            icon = status_icons.get(task["status"], "[?]")
            rows.append([
                task["directory_name"],
                task["type"].upper(),
                f"{icon} {task['status'].title()}",
                task.get("submitted_at", "-") or "-",
            ])

        Display.table(
            "Directory Status",
            columns=[
                {"name": "Directory", "style": "cyan"},
                {"name": "Type", "style": "yellow"},
                {"name": "Status"},
                {"name": "Submitted At", "style": "dim"},
            ],
            rows=rows,
        )

        return plan

    # ── AI-Generated Submission Content ──────────────────────────────

    def generate_listing_content(
        self,
        domain: str,
        business_name: str,
        business_description: str = "",
        provider_name: Optional[str] = None,
    ) -> dict[str, str]:
        """
        Generate optimised business listing content using AI.

        Returns:
            Dict with short_description, long_description, tagline, categories.
        """
        from rankforge.ai.base import get_ai_provider

        provider = get_ai_provider(provider_name)

        prompt = (
            f"Generate optimised business directory listing content for:\n"
            f"- Domain: {domain}\n"
            f"- Business Name: {business_name}\n"
            f"- Description: {business_description or 'Not provided'}\n\n"
            f"Provide:\n"
            f"1. Tagline (under 10 words)\n"
            f"2. Short description (under 50 words) -- for directories with character limits\n"
            f"3. Long description (150-200 words) -- detailed, keyword-rich\n"
            f"4. Suggested categories (5 relevant business categories)\n"
            f"5. Suggested keywords (10 relevant keywords to use across listings)\n\n"
            f"Format each section clearly with labels."
        )

        raw = provider.generate_content(prompt)
        Display.section("AI-Generated Listing Content")
        Display.markdown(raw)

        return {
            "domain": domain,
            "business_name": business_name,
            "content": raw,
            "generated_at": datetime.now().isoformat(),
        }

    # ── Export ────────────────────────────────────────────────────────

    def export_plan(self, domain: str) -> Optional[dict[str, str]]:
        """Export the submission plan to JSON and CSV."""
        plan = self.memory.retrieve("submissions", domain)
        if not plan:
            Display.error(f"No plan found for '{domain}'")
            return None

        json_path = self.exporter.to_json(plan, prefix=f"submissions_{domain}")
        csv_path = self.exporter.to_csv(plan, prefix=f"submissions_{domain}")

        Display.success(f"Exported:\n  JSON: {json_path}\n  CSV:  {csv_path}")
        return {"json": str(json_path), "csv": str(csv_path)}
