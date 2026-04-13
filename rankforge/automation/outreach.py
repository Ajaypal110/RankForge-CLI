"""
RankForge CLI - Outreach Manager
===================================
Generate personalised outreach emails for link building,
manage outreach campaigns, and track results.
"""

import json
from datetime import datetime
from typing import Any, Optional

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger
from rankforge.utils.display import Display
from rankforge.utils.export import Exporter
from rankforge.database.memory import ProjectMemory

logger = get_logger("rankforge.automation.outreach")


class OutreachManager:
    """
    AI-powered outreach email generator and campaign manager.

    Generates personalised emails for guest posting, link exchanges,
    and broken link building campaigns.
    """

    TEMPLATES = {
        "guest_post": (
            "Write a professional outreach email to {contact_name} at {target_site}. "
            "I run {your_site}, a website about {your_niche}. I'd like to propose a "
            "guest post about '{topic}'. Mention that I've read their content and found "
            "it valuable. Keep it under 200 words, friendly, and persuasive. "
            "Include a subject line."
        ),
        "link_exchange": (
            "Write a brief, friendly email to {contact_name} at {target_site}. "
            "I run {your_site} in the {your_niche} space. I noticed we cover similar "
            "topics and think a link exchange could benefit both our audiences. "
            "Keep it under 150 words with a clear CTA. Include a subject line."
        ),
        "broken_link": (
            "Write a helpful outreach email to {contact_name} at {target_site}. "
            "I found a broken link on their page '{broken_page}' that previously "
            "pointed to a resource about '{topic}'. I have a similar resource at "
            "{your_url} that could be a good replacement. Be helpful, not pushy. "
            "Under 150 words. Include a subject line."
        ),
        "resource_page": (
            "Write a brief email to {contact_name} at {target_site}. "
            "I noticed their resource page about '{topic}' and I have a highly "
            "relevant resource at {your_url} about {your_niche} that their audience "
            "would find valuable. Explain why it would be a good fit. "
            "Under 150 words. Include a subject line."
        ),
    }

    def __init__(self, project_name: str = "default"):
        self.memory = ProjectMemory(project_name)
        self.exporter = Exporter("outreach")

    # ── Email Generation ─────────────────────────────────────────────

    def generate_email(
        self,
        template_type: str = "guest_post",
        variables: Optional[dict[str, str]] = None,
        custom_prompt: Optional[str] = None,
        provider_name: Optional[str] = None,
    ) -> dict[str, str]:
        """
        Generate a personalised outreach email.

        Args:
            template_type: One of: guest_post, link_exchange, broken_link, resource_page.
            variables: Dict of template variables (target_site, your_site, etc.).
            custom_prompt: Override the template with a custom prompt.
            provider_name: AI provider to use (openai, claude, gemini).

        Returns:
            Dict with 'subject' and 'body' keys.
        """
        from rankforge.ai.base import get_ai_provider

        provider = get_ai_provider(provider_name)

        if custom_prompt:
            prompt = custom_prompt
        else:
            template = self.TEMPLATES.get(template_type)
            if not template:
                raise ValueError(f"Unknown template: {template_type}. Options: {list(self.TEMPLATES.keys())}")

            # Fill in template variables with defaults
            defaults = {
                "contact_name": "the webmaster",
                "target_site": "your website",
                "your_site": "my website",
                "your_niche": "digital marketing",
                "topic": "SEO best practices",
                "your_url": "https://example.com",
                "broken_page": "your resources page",
            }
            vars_merged = {**defaults, **(variables or {})}
            prompt = template.format(**vars_merged)

        raw = provider.generate_content(prompt)

        # Parse subject and body
        subject = ""
        body = raw
        lines = raw.strip().split("\n")
        for i, line in enumerate(lines):
            if line.lower().startswith("subject:") or line.lower().startswith("subject line:"):
                subject = line.split(":", 1)[1].strip().strip('"').strip("'")
                body = "\n".join(lines[i + 1:]).strip()
                break

        return {"subject": subject, "body": body, "template_type": template_type}

    # ── Batch Generation ─────────────────────────────────────────────

    def generate_batch(
        self,
        targets: list[dict[str, str]],
        template_type: str = "guest_post",
        provider_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Generate outreach emails for multiple targets.

        Args:
            targets: List of dicts, each with target_site, contact_name, etc.
            template_type: Template to use for all emails.

        Returns:
            List of generated email dicts.
        """
        Display.section(f"Batch Outreach Generation ({len(targets)} targets)")

        results = []
        for i, target in enumerate(targets, 1):
            with Display.spinner(f"[{i}/{len(targets)}] Generating email for {target.get('target_site', 'unknown')}...") as progress:
                progress.add_task("gen", total=None)
                try:
                    email = self.generate_email(
                        template_type=template_type,
                        variables=target,
                        provider_name=provider_name,
                    )
                    email["target"] = target
                    email["status"] = "generated"
                    email["generated_at"] = datetime.now().isoformat()
                    results.append(email)
                    Display.success(f"Generated: {email.get('subject', 'N/A')[:50]}")
                except Exception as exc:
                    logger.error("Failed for %s: %s", target.get("target_site"), exc)
                    results.append({"target": target, "status": "failed", "error": str(exc)})
                    Display.error(f"Failed: {exc}")

        # Save to memory
        self.memory.store("outreach", f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}", results)

        return results

    # ── Interactive Generation ───────────────────────────────────────

    def interactive_generate(self, provider_name: Optional[str] = None) -> dict[str, str]:
        """
        Interactive outreach email generation with user prompts.

        Returns:
            Generated email dict.
        """
        from rich.prompt import Prompt

        Display.section("Interactive Outreach Email Generator")

        # Choose template
        Display.info("Available templates:")
        for i, (key, _) in enumerate(self.TEMPLATES.items(), 1):
            Display.info(f"  {i}. {key.replace('_', ' ').title()}")

        template_choice = Prompt.ask(
            "Choose template",
            choices=[str(i) for i in range(1, len(self.TEMPLATES) + 1)],
            default="1",
        )
        template_type = list(self.TEMPLATES.keys())[int(template_choice) - 1]

        # Gather variables
        variables = {}
        variables["target_site"] = Prompt.ask("Target website", default="example.com")
        variables["contact_name"] = Prompt.ask("Contact name", default="the webmaster")
        variables["your_site"] = Prompt.ask("Your website", default="mysite.com")
        variables["your_niche"] = Prompt.ask("Your niche", default="digital marketing")
        variables["topic"] = Prompt.ask("Topic/subject", default="SEO best practices")

        with Display.spinner("Generating personalised email...") as progress:
            progress.add_task("gen", total=None)
            email = self.generate_email(
                template_type=template_type,
                variables=variables,
                provider_name=provider_name,
            )

        Display.section("Generated Email")
        if email["subject"]:
            Display.key_value({"Subject": email["subject"]})
        Display.markdown(email["body"])

        return email

    # ── Export Campaign ──────────────────────────────────────────────

    def export_campaign(self, emails: list[dict[str, Any]], prefix: str = "outreach_campaign") -> dict[str, str]:
        """Export generated emails to both JSON and CSV."""
        json_path = self.exporter.to_json(emails, prefix=prefix)

        # Flatten for CSV
        csv_rows = []
        for e in emails:
            target = e.get("target", {})
            csv_rows.append({
                "target_site": target.get("target_site", ""),
                "contact_name": target.get("contact_name", ""),
                "subject": e.get("subject", ""),
                "body": e.get("body", "")[:500],
                "template_type": e.get("template_type", ""),
                "status": e.get("status", ""),
                "generated_at": e.get("generated_at", ""),
            })

        csv_path = self.exporter.to_csv(csv_rows, prefix=prefix)
        Display.success(f"Exported to:\n  JSON: {json_path}\n  CSV:  {csv_path}")
        return {"json": str(json_path), "csv": str(csv_path)}
