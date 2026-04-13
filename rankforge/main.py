"""
RankForge CLI -- Main Entry Point
====================================
A production-ready CLI application combining AI capabilities,
SEO tools, and automation for off-page SEO.

Built with Typer + Rich for a premium terminal experience.

Usage:
    python main.py --help
    python main.py keyword "seo services"
    python main.py backlinks example.com
    python main.py serp "best seo tools"
    python main.py audit example.com
    python main.py competitors example.com
    python main.py article "How to do keyword research"
    python main.py outreach
    python main.py auto-build example.com
    python main.py ai "Write a meta description for a landing page"
"""

import json
from typing import Optional

import typer
from rich.console import Console

from rankforge import __version__
from rankforge.utils.display import Display
from rankforge.utils.export import Exporter
from rankforge.utils.logger import get_logger
from rankforge.database.memory import ProjectMemory

logger = get_logger("rankforge.cli")
console = Console(highlight=False)

# ── Typer App ────────────────────────────────────────────────────────
app = typer.Typer(
    name="rankforge",
    help="RankForge CLI -- AI-powered SEO toolkit for the terminal.",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


# ── Helper: Banner ───────────────────────────────────────────────────
def _show_banner() -> None:
    """Print the RankForge startup banner."""
    Display.header("RankForge CLI", f"v{__version__}  |  AI-Powered SEO Toolkit")


# =====================================================================
#  KEYWORD RESEARCH
# =====================================================================

@app.command("keyword")
def keyword_cmd(
    query: str = typer.Argument(..., help="Seed keyword or phrase to research."),
    no_ai: bool = typer.Option(False, "--no-ai", help="Skip AI-powered keyword expansion."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider: openai, claude, gemini."),
    export: bool = typer.Option(False, "--export", "-e", help="Export results to JSON/CSV."),
    project: str = typer.Option("default", "--project", help="Project name for memory storage."),
) -> None:
    """Research keywords -- autocomplete, SerpAPI, and AI expansion."""
    _show_banner()

    from rankforge.seo.keywords import KeywordResearcher

    researcher = KeywordResearcher()
    results = researcher.research(query, use_ai=not no_ai, ai_provider=provider)

    # Store in project memory
    memory = ProjectMemory(project)
    memory.store("keywords", query, results)
    Display.success(f"Results saved to project '{project}' memory.")

    if export:
        exporter = Exporter("keywords")
        path = exporter.to_json(results, prefix=f"keywords_{query[:30]}")
        Display.success(f"Exported -> {path}")


# =====================================================================
#  BACKLINK ANALYSIS
# =====================================================================

@app.command("backlinks")
def backlinks_cmd(
    domain: str = typer.Argument(..., help="Domain to analyse backlinks for."),
    export: bool = typer.Option(False, "--export", "-e", help="Export results."),
    project: str = typer.Option("default", "--project", help="Project name."),
) -> None:
    """Analyse backlink profile -- DataForSEO or AI simulation."""
    _show_banner()

    from rankforge.seo.backlinks import BacklinkAnalyzer

    analyzer = BacklinkAnalyzer()
    results = analyzer.analyze(domain)

    memory = ProjectMemory(project)
    memory.store("backlinks", domain, results)
    Display.success(f"Results saved to project '{project}' memory.")

    if export:
        exporter = Exporter("backlinks")
        path = exporter.to_json(results, prefix=f"backlinks_{domain}")
        Display.success(f"Exported -> {path}")


# =====================================================================
#  SERP ANALYSIS
# =====================================================================

@app.command("serp")
def serp_cmd(
    query: str = typer.Argument(..., help="Search query to analyse SERPs for."),
    num: int = typer.Option(10, "--num", "-n", help="Number of results to fetch."),
    export: bool = typer.Option(False, "--export", "-e", help="Export results."),
    project: str = typer.Option("default", "--project", help="Project name."),
) -> None:
    """Analyse search engine results pages."""
    _show_banner()

    from rankforge.seo.serp import SerpAnalyzer

    analyzer = SerpAnalyzer()
    results = analyzer.analyze(query, num_results=num)

    memory = ProjectMemory(project)
    memory.store("serp", query, results)
    Display.success(f"Results saved to project '{project}' memory.")

    if export:
        exporter = Exporter("serp")
        path = exporter.to_json(results, prefix=f"serp_{query[:30]}")
        Display.success(f"Exported -> {path}")


# =====================================================================
#  SITE AUDIT
# =====================================================================

@app.command("audit")
def audit_cmd(
    domain: str = typer.Argument(..., help="Domain or URL to audit."),
    export: bool = typer.Option(False, "--export", "-e", help="Export results."),
    project: str = typer.Option("default", "--project", help="Project name."),
) -> None:
    """Run an on-page SEO audit with scoring."""
    _show_banner()

    from rankforge.seo.audit import SiteAuditor

    auditor = SiteAuditor()
    results = auditor.audit(domain)

    memory = ProjectMemory(project)
    memory.store("audits", domain, results)
    Display.success(f"Audit saved to project '{project}' memory.")

    if export:
        exporter = Exporter("audits")
        path = exporter.to_json(results, prefix=f"audit_{domain}")
        Display.success(f"Exported -> {path}")


# =====================================================================
#  COMPETITOR ANALYSIS
# =====================================================================

@app.command("competitors")
def competitors_cmd(
    domain: str = typer.Argument(..., help="Your domain to find competitors for."),
    keywords: Optional[str] = typer.Option(None, "--keywords", "-k", help="Comma-separated niche keywords."),
    no_ai: bool = typer.Option(False, "--no-ai", help="Skip AI insights."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider."),
    export: bool = typer.Option(False, "--export", "-e", help="Export results."),
    project: str = typer.Option("default", "--project", help="Project name."),
) -> None:
    """Analyse competitors -- SERP discovery + AI strategic insights."""
    _show_banner()

    from rankforge.seo.competitors import CompetitorAnalyzer

    analyzer = CompetitorAnalyzer()
    kw_list = [k.strip() for k in keywords.split(",")] if keywords else None
    results = analyzer.analyze(
        domain, niche_keywords=kw_list, use_ai=not no_ai, ai_provider=provider
    )

    memory = ProjectMemory(project)
    memory.store("competitors", domain, results)
    Display.success(f"Results saved to project '{project}' memory.")

    if export:
        exporter = Exporter("competitors")
        path = exporter.to_json(results, prefix=f"competitors_{domain}")
        Display.success(f"Exported -> {path}")


# =====================================================================
#  AI CONTENT GENERATION
# =====================================================================

@app.command("ai")
def ai_cmd(
    prompt: str = typer.Argument(..., help="Prompt for AI content generation."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider: openai, claude, gemini."),
    max_tokens: int = typer.Option(2048, "--max-tokens", "-m", help="Max tokens to generate."),
) -> None:
    """Generate content using AI (GPT, Claude, or Gemini)."""
    _show_banner()

    from rankforge.ai.base import get_ai_provider

    provider_instance = get_ai_provider(provider)
    Display.section(f"AI Generation ({provider_instance.name})")

    with Display.spinner("Generating content...") as progress:
        progress.add_task("generate", total=None)
        result = provider_instance.generate_content(prompt, max_tokens=max_tokens)

    Display.markdown(result)


# =====================================================================
#  INTERACTIVE CHAT MEMORY REPL
# =====================================================================

@app.command("chat")
def chat_cmd(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider: openai, claude, gemini."),
) -> None:
    """Start an interactive chat session with AI memory."""
    _show_banner()

    from rankforge.ai.base import get_ai_provider
    import rich.prompt
    
    try:
        provider_instance = get_ai_provider(provider)
    except Exception as e:
        Display.error(str(e))
        return

    Display.section(f"Interactive Chat ({provider_instance.name})")
    Display.info("Type 'exit' or 'quit' to end the session.\n")

    messages = []

    while True:
        try:
            user_input = rich.prompt.Prompt.ask("\\[cyan]You\\[/cyan]")
            
            if user_input.strip().lower() in ("exit", "quit"):
                Display.success("Chat ended.")
                break
                
            if not user_input.strip():
                continue

            messages.append({"role": "user", "content": user_input})
            
            with Display.spinner("Thinking...") as progress:
                progress.add_task("gen", total=None)
                response = provider_instance.chat(messages)

            messages.append({"role": "assistant", "content": response})
            
            console.print(f"\n\\[green]AI:\\[/green]\n{response}\n")

        except KeyboardInterrupt:
            Display.success("\nChat ended.")
            break
        except Exception as e:
            Display.error(f"\nError connecting to AI: {e}")
            break


# =====================================================================
#  ARTICLE GENERATION
# =====================================================================

@app.command("article")
def article_cmd(
    topic: str = typer.Argument(..., help="Article topic."),
    words: int = typer.Option(1500, "--words", "-w", help="Target word count."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider."),
    export: bool = typer.Option(False, "--export", "-e", help="Export the article."),
) -> None:
    """Generate an SEO-optimised long-form article."""
    _show_banner()

    from rankforge.ai.base import get_ai_provider

    provider_instance = get_ai_provider(provider)
    Display.section(f"Article Generation: '{topic}'")

    with Display.spinner("Writing article...") as progress:
        progress.add_task("write", total=None)
        article = provider_instance.generate_article(topic, word_count=words)

    Display.markdown(article)

    if export:
        exporter = Exporter("articles")
        path = exporter.to_json(
            {"topic": topic, "word_count": words, "content": article},
            prefix=f"article_{topic[:30]}",
        )
        Display.success(f"Article exported -> {path}")


# =====================================================================
#  OUTREACH
# =====================================================================

@app.command("outreach")
def outreach_cmd(
    target_site: Optional[str] = typer.Option(None, "--target", "-t", help="Target website."),
    your_site: Optional[str] = typer.Option(None, "--site", "-s", help="Your website."),
    niche: Optional[str] = typer.Option(None, "--niche", help="Your niche."),
    topic: Optional[str] = typer.Option(None, "--topic", help="Proposed topic."),
    template: str = typer.Option("guest_post", "--template", help="Template: guest_post, link_exchange, broken_link, resource_page."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider."),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode."),
    project: str = typer.Option("default", "--project", help="Project name."),
) -> None:
    """Generate outreach emails for link building."""
    _show_banner()

    from rankforge.automation.outreach import OutreachManager

    manager = OutreachManager(project_name=project)

    if interactive:
        manager.interactive_generate(provider_name=provider)
    else:
        variables = {}
        if target_site:
            variables["target_site"] = target_site
        if your_site:
            variables["your_site"] = your_site
        if niche:
            variables["your_niche"] = niche
        if topic:
            variables["topic"] = topic

        with Display.spinner("Generating outreach email...") as progress:
            progress.add_task("gen", total=None)
            email = manager.generate_email(
                template_type=template,
                variables=variables,
                provider_name=provider,
            )

        Display.section("Generated Outreach Email")
        if email["subject"]:
            Display.key_value({"Subject": email["subject"]})
        Display.markdown(email["body"])


# =====================================================================
#  GUEST POST FINDER
# =====================================================================

@app.command("find-guest-posts")
def find_guest_posts_cmd(
    niche: str = typer.Argument(..., help="Niche/topic to find guest post opportunities."),
    max_results: int = typer.Option(30, "--max", "-m", help="Maximum results to find."),
    enrich: bool = typer.Option(False, "--enrich", help="Extract contact info from results."),
    export: bool = typer.Option(False, "--export", "-e", help="Export results."),
    project: str = typer.Option("default", "--project", help="Project name."),
) -> None:
    """Find guest posting opportunities via search footprints."""
    _show_banner()

    from rankforge.automation.scraper import GuestPostFinder

    finder = GuestPostFinder()
    opportunities = finder.find_guest_post_sites(niche, max_results=max_results)

    if enrich and opportunities:
        opportunities = finder.enrich_opportunities(opportunities)

    memory = ProjectMemory(project)
    memory.store("guest_posts", niche, opportunities)

    if export and opportunities:
        exporter = Exporter("guest_posts")
        path_json = exporter.to_json(opportunities, prefix=f"guest_posts_{niche[:20]}")
        path_csv = exporter.to_csv(opportunities, prefix=f"guest_posts_{niche[:20]}")
        Display.success(f"Exported -> {path_json}\n          -> {path_csv}")


# =====================================================================
#  DIRECTORY SUBMISSIONS
# =====================================================================

@app.command("submit-plan")
def submit_plan_cmd(
    domain: str = typer.Argument(..., help="Your domain."),
    business_name: Optional[str] = typer.Option(None, "--name", "-n", help="Business name."),
    export: bool = typer.Option(False, "--export", "-e", help="Export the plan."),
    project: str = typer.Option("default", "--project", help="Project name."),
) -> None:
    """Generate a directory submission plan."""
    _show_banner()

    from rankforge.automation.submission import SubmissionManager

    manager = SubmissionManager(project_name=project)
    manager.generate_plan(domain, business_name=business_name or domain)

    if export:
        manager.export_plan(domain)


# =====================================================================
#  AUTO-BUILD (Pipeline)
# =====================================================================

@app.command("auto-build")
def auto_build_cmd(
    domain: str = typer.Argument(..., help="Domain to run the full pipeline for."),
    keywords: Optional[str] = typer.Option(None, "--keywords", "-k", help="Comma-separated seed keywords."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider."),
    export: bool = typer.Option(True, "--export/--no-export", help="Export all results."),
    project: str = typer.Option("default", "--project", help="Project name."),
) -> None:
    """Run the full SEO pipeline -- audit, keywords, competitors, backlinks, outreach plan."""
    _show_banner()
    Display.section("AUTO-BUILD: Full SEO Pipeline")
    Display.info(f"Running complete analysis for: {domain}")

    memory = ProjectMemory(project)
    exporter = Exporter(f"auto_build_{domain}")
    pipeline_results: dict = {"domain": domain, "steps": {}}

    # ── Step 1: Site Audit ───────────────────────────────────────────
    Display.header("Step 1/5", "Site Audit")
    try:
        from rankforge.seo.audit import SiteAuditor

        auditor = SiteAuditor()
        audit_results = auditor.audit(domain)
        pipeline_results["steps"]["audit"] = audit_results
        memory.store("auto_build_audit", domain, audit_results)
        Display.success("Site audit complete.")
    except Exception as exc:
        Display.error(f"Audit failed: {exc}")
        pipeline_results["steps"]["audit"] = {"error": str(exc)}

    # ── Step 2: Keyword Research ─────────────────────────────────────
    Display.header("Step 2/5", "Keyword Research")
    try:
        from rankforge.seo.keywords import KeywordResearcher

        researcher = KeywordResearcher()
        seed_keywords = [k.strip() for k in keywords.split(",")] if keywords else [domain.replace("www.", "").split(".")[0]]
        kw_results = {}
        for kw in seed_keywords[:3]:
            kw_results[kw] = researcher.research(kw, use_ai=True, ai_provider=provider)
        pipeline_results["steps"]["keywords"] = kw_results
        memory.store("auto_build_keywords", domain, kw_results)
        Display.success("Keyword research complete.")
    except Exception as exc:
        Display.error(f"Keyword research failed: {exc}")
        pipeline_results["steps"]["keywords"] = {"error": str(exc)}

    # ── Step 3: Backlink Analysis ────────────────────────────────────
    Display.header("Step 3/5", "Backlink Analysis")
    try:
        from rankforge.seo.backlinks import BacklinkAnalyzer

        analyzer = BacklinkAnalyzer()
        bl_results = analyzer.analyze(domain)
        pipeline_results["steps"]["backlinks"] = bl_results
        memory.store("auto_build_backlinks", domain, bl_results)
        Display.success("Backlink analysis complete.")
    except Exception as exc:
        Display.error(f"Backlink analysis failed: {exc}")
        pipeline_results["steps"]["backlinks"] = {"error": str(exc)}

    # ── Step 4: Competitor Analysis ──────────────────────────────────
    Display.header("Step 4/5", "Competitor Analysis")
    try:
        from rankforge.seo.competitors import CompetitorAnalyzer

        comp = CompetitorAnalyzer()
        kw_list = [k.strip() for k in keywords.split(",")] if keywords else None
        comp_results = comp.analyze(domain, niche_keywords=kw_list, use_ai=True, ai_provider=provider)
        pipeline_results["steps"]["competitors"] = comp_results
        memory.store("auto_build_competitors", domain, comp_results)
        Display.success("Competitor analysis complete.")
    except Exception as exc:
        Display.error(f"Competitor analysis failed: {exc}")
        pipeline_results["steps"]["competitors"] = {"error": str(exc)}

    # ── Step 5: Directory Submission Plan ────────────────────────────
    Display.header("Step 5/5", "Submission Plan")
    try:
        from rankforge.automation.submission import SubmissionManager

        sub_mgr = SubmissionManager(project_name=project)
        sub_plan = sub_mgr.generate_plan(domain)
        pipeline_results["steps"]["submission_plan"] = sub_plan
        Display.success("Submission plan generated.")
    except Exception as exc:
        Display.error(f"Submission plan failed: {exc}")
        pipeline_results["steps"]["submission_plan"] = {"error": str(exc)}

    # ── Export Everything ────────────────────────────────────────────
    if export:
        path = exporter.to_json(pipeline_results, prefix="auto_build_full")
        Display.success(f"Full pipeline results exported -> {path}")

    # ── Summary ──────────────────────────────────────────────────────
    Display.section("Auto-Build Complete")
    step_status = []
    for step_name, step_data in pipeline_results["steps"].items():
        status = "[X] Failed" if isinstance(step_data, dict) and "error" in step_data else "[+] Done"
        step_status.append([step_name.replace("_", " ").title(), status])

    Display.table(
        "Pipeline Summary",
        columns=[
            {"name": "Step", "style": "cyan"},
            {"name": "Status"},
        ],
        rows=step_status,
    )


# =====================================================================
#  MEMORY / HISTORY
# =====================================================================

@app.command("history")
def history_cmd(
    project: str = typer.Option("default", "--project", help="Project name."),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category."),
) -> None:
    """View stored results from project memory."""
    _show_banner()

    memory = ProjectMemory(project)

    if category:
        keys = memory.list_keys(category)
        Display.section(f"Project '{project}' -- {category}")
        if keys:
            Display.table(
                f"Stored Keys ({category})",
                columns=[
                    {"name": "#", "style": "dim", "justify": "right"},
                    {"name": "Key", "style": "cyan"},
                ],
                rows=[[str(i + 1), k] for i, k in enumerate(keys)],
            )
        else:
            Display.warning(f"No entries in category '{category}'.")
    else:
        categories = memory.list_categories()
        Display.section(f"Project '{project}' -- All Categories")
        if categories:
            for cat in categories:
                keys = memory.list_keys(cat)
                Display.info(f"  {cat}: {len(keys)} entries")
        else:
            Display.warning("No stored data yet. Run some commands first!")


# =====================================================================
#  SEO META GENERATION
# =====================================================================

@app.command("meta")
def meta_cmd(
    title: str = typer.Argument(..., help="Page title."),
    summary: str = typer.Option("", "--summary", "-s", help="Page content summary."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider."),
) -> None:
    """Generate SEO meta title and description."""
    _show_banner()

    from rankforge.ai.base import get_ai_provider

    ai = get_ai_provider(provider)

    with Display.spinner("Generating meta tags...") as progress:
        progress.add_task("meta", total=None)
        result = ai.generate_seo_meta(title, summary or title)

    Display.section("Generated Meta Tags")
    Display.markdown(result)


# =====================================================================
#  ANCHOR TEXT GENERATION
# =====================================================================

@app.command("anchors")
def anchors_cmd(
    url: str = typer.Argument(..., help="Target URL for anchor text."),
    context: str = typer.Option("SEO", "--context", "-c", help="Content context."),
    count: int = typer.Option(5, "--count", "-n", help="Number of suggestions."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider."),
) -> None:
    """Generate natural anchor text variations."""
    _show_banner()

    from rankforge.ai.base import get_ai_provider

    ai = get_ai_provider(provider)

    with Display.spinner("Generating anchor text...") as progress:
        progress.add_task("anchors", total=None)
        result = ai.generate_anchor_text(url, context, count)

    Display.section("Anchor Text Suggestions")
    Display.markdown(result)


# =====================================================================
#  CACHE MANAGEMENT
# =====================================================================

@app.command("clear-cache")
def clear_cache_cmd() -> None:
    """Clear all cached API responses."""
    _show_banner()

    from rankforge.utils.cache import Cache
    import shutil
    from pathlib import Path

    cache_dir = Path(settings.cache_dir)
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        Display.success("Cache cleared successfully.")
    else:
        Display.info("Cache directory does not exist -- nothing to clear.")


# =====================================================================
#  VERSION
# =====================================================================

@app.command("version")
def version_cmd() -> None:
    """Show RankForge CLI version."""
    _show_banner()


# =====================================================================
#  ENTRY POINT
# =====================================================================

# Need settings import at top level for clear-cache
from rankforge.config.settings import settings  # noqa: E402

if __name__ == "__main__":
    app()
