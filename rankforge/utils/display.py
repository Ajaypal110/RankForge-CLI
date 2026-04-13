"""
RankForge CLI - Display Module
================================
Pretty-printing helpers using Rich for tables, panels, and progress bars.
"""

import io
import os
import sys
from typing import Any

# Force UTF-8 stdout on Windows to avoid cp1252 encoding crashes
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich import box

console = Console(force_terminal=True)


class Display:
    """Static helper methods for rich CLI output."""

    # -- Headings & Panels ----------------------------------------------------

    @staticmethod
    def header(title: str, subtitle: str = "") -> None:
        """Print a large branded header panel."""
        text = f"[bold bright_cyan]{title}[/]"
        if subtitle:
            text += f"\n[dim]{subtitle}[/]"
        console.print(
            Panel(text, border_style="bright_cyan", box=box.DOUBLE_EDGE, padding=(1, 3))
        )

    @staticmethod
    def section(title: str) -> None:
        """Print a section divider."""
        console.print(f"\n[bold yellow]--- {title} ---[/]\n")

    @staticmethod
    def success(msg: str) -> None:
        console.print(f"[bold green][+][/] {msg}")

    @staticmethod
    def warning(msg: str) -> None:
        console.print(f"[bold yellow][!][/] {msg}")

    @staticmethod
    def error(msg: str) -> None:
        console.print(f"[bold red][X][/] {msg}")

    @staticmethod
    def info(msg: str) -> None:
        console.print(f"[bold blue][*][/] {msg}")

    # -- Tables ---------------------------------------------------------------

    @staticmethod
    def table(
        title: str,
        columns: list[dict[str, Any]],
        rows: list[list[str]],
    ) -> None:
        """
        Render a Rich table.

        Args:
            title: Table title.
            columns: List of dicts with keys: name, style (optional), justify (optional).
            rows: List of row data (list of strings).
        """
        tbl = Table(
            title=f"[bold]{title}[/]",
            box=box.ROUNDED,
            border_style="bright_cyan",
            header_style="bold magenta",
            show_lines=True,
        )
        for col in columns:
            tbl.add_column(
                col["name"],
                style=col.get("style", ""),
                justify=col.get("justify", "left"),
            )
        for row in rows:
            tbl.add_row(*row)
        console.print(tbl)

    # -- Markdown / Code ------------------------------------------------------

    @staticmethod
    def markdown(text: str) -> None:
        """Render markdown text in the terminal."""
        console.print(Markdown(text))

    @staticmethod
    def code(code: str, language: str = "python") -> None:
        """Render syntax-highlighted code."""
        console.print(Syntax(code, language, theme="monokai", line_numbers=True))

    # -- JSON -----------------------------------------------------------------

    @staticmethod
    def json(data: Any) -> None:
        """Pretty-print a dict/list as JSON."""
        import json as _json

        console.print_json(_json.dumps(data, indent=2, default=str))

    # -- Spinner Context Manager ----------------------------------------------

    @staticmethod
    def spinner(message: str = "Working...") -> Progress:
        """
        Return a Rich Progress context manager with a spinner.

        Usage:
            with Display.spinner("Fetching data...") as progress:
                task = progress.add_task("fetch", total=None)
                # ... do work ...
        """
        return Progress(
            SpinnerColumn(style="bright_cyan"),
            TextColumn("[bold]{task.description}"),
            console=console,
            transient=True,
        )

    # -- Key-Value Pairs ------------------------------------------------------

    @staticmethod
    def key_value(pairs: dict[str, Any], title: str = "") -> None:
        """Display key-value pairs in a neat panel."""
        lines = []
        for k, v in pairs.items():
            lines.append(f"[bold cyan]{k}:[/] {v}")
        content = "\n".join(lines)
        if title:
            console.print(Panel(content, title=f"[bold]{title}[/]", border_style="blue"))
        else:
            console.print(content)
