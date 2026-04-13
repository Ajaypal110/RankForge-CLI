<div align="center">

# ⚒ RankForge CLI

### AI-Powered SEO Toolkit for the Terminal

**Keyword Research • Backlink Analysis • Site Audits • Competitor Intelligence • AI Content • Outreach Automation**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CLI: Typer](https://img.shields.io/badge/CLI-Typer-purple.svg)](https://typer.tiangolo.com)

</div>

---

## 🚀 What is RankForge?

RankForge CLI is a **terminal-based SEO power tool** that combines the capabilities of SEMrush, Ubersuggest, and an AI writing assistant — all from your command line. It's designed for SEO professionals, digital marketers, and developers who want fast, scriptable, and automatable SEO workflows.

### Key Features

| Feature | Description |
|---------|-------------|
| 🔍 **Keyword Research** | Google Autocomplete, SerpAPI, and AI-powered keyword expansion |
| 🔗 **Backlink Analysis** | DataForSEO integration with AI simulation fallback |
| 📊 **SERP Analysis** | Analyse top results, SERP features, and People Also Ask |
| 🩺 **Site Audit** | On-page SEO scoring: meta tags, headings, images, links, performance |
| 🏆 **Competitor Analysis** | SERP-based competitor discovery + AI strategic insights |
| 📝 **AI Article Writer** | SEO-optimised long-form content via GPT, Claude, or Gemini |
| 📧 **Outreach Generator** | AI-powered personalised outreach emails for link building |
| 🔎 **Guest Post Finder** | Footprint-based guest post opportunity discovery |
| 📋 **Submission Planner** | Directory submission plan with progress tracking |
| 🚀 **Auto-Build Pipeline** | Run all tools in sequence for a complete SEO analysis |

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/rankforge-cli.git
cd rankforge-cli
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install as a package (recommended):

```bash
pip install -e .
```

### 4. Configure Environment

```bash
copy .env.example .env
# Edit .env and add your API keys
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and add your API keys. **All keys are optional** — the tool gracefully degrades without them:

| Key | Provider | Purpose | Required? |
|-----|----------|---------|-----------|
| `OPENAI_API_KEY` | OpenAI | GPT content generation | For AI features |
| `ANTHROPIC_API_KEY` | Anthropic | Claude content generation | For AI features |
| `GOOGLE_API_KEY` | Google | Gemini content generation | For AI features |
| `SERPAPI_KEY` | SerpAPI | SERP data & keyword research | For SERP/keyword data |
| `DATAFORSEO_LOGIN` | DataForSEO | Backlink data | For backlink analysis |
| `DATAFORSEO_PASSWORD` | DataForSEO | Backlink data | For backlink analysis |

> **Tip**: You only need **one** AI provider key to use AI features. The tool defaults to OpenAI but can be switched with `--provider claude` or `--provider gemini`.

---

## 🎯 Usage

### Quick Start

```bash
# Run via Python
python -m rankforge.main --help

# Or if installed as package
rankforge --help
```

### All Commands

#### 🔍 Keyword Research
```bash
# Basic keyword research with AI expansion
python -m rankforge.main keyword "seo services"

# Without AI (autocomplete only)
python -m rankforge.main keyword "seo services" --no-ai

# With specific AI provider and export
python -m rankforge.main keyword "seo services" --provider claude --export

# Save to a named project
python -m rankforge.main keyword "seo services" --project my-site
```

#### 🔗 Backlink Analysis
```bash
# Analyse backlinks (DataForSEO or AI simulation)
python -m rankforge.main backlinks example.com

# Export results
python -m rankforge.main backlinks example.com --export
```

#### 📊 SERP Analysis
```bash
# Analyse search results for a query
python -m rankforge.main serp "best seo tools"

# Get more results
python -m rankforge.main serp "best seo tools" --num 20
```

#### 🩺 Site Audit
```bash
# Run on-page SEO audit
python -m rankforge.main audit example.com

# Audit a specific URL
python -m rankforge.main audit https://example.com/blog
```

#### 🏆 Competitor Analysis
```bash
# Basic competitor analysis
python -m rankforge.main competitors example.com

# With specific niche keywords
python -m rankforge.main competitors example.com -k "seo tools,rank tracker,keyword research"

# Skip AI insights
python -m rankforge.main competitors example.com --no-ai
```

#### 🤖 AI Content Generation
```bash
# Free-form AI generation
python -m rankforge.main ai "Write 5 meta descriptions for an SEO agency"

# Generate with Claude
python -m rankforge.main ai "Explain topical authority" --provider claude

# Generate with Gemini
python -m rankforge.main ai "Create a content calendar for Q1" --provider gemini
```

#### 📝 Article Generation
```bash
# Generate an SEO article
python -m rankforge.main article "How to do keyword research in 2025"

# Longer article with export
python -m rankforge.main article "Complete guide to technical SEO" --words 3000 --export
```

#### 📧 Outreach Email
```bash
# Quick outreach email
python -m rankforge.main outreach --target example.com --site mysite.com --topic "SEO tips"

# Interactive mode (prompts for all info)
python -m rankforge.main outreach --interactive

# Broken link template
python -m rankforge.main outreach --template broken_link --target blog.com --site mysite.com
```

#### 🔎 Guest Post Finder
```bash
# Find guest post opportunities
python -m rankforge.main find-guest-posts "digital marketing"

# Find and extract contact info
python -m rankforge.main find-guest-posts "seo" --enrich --export
```

#### 📋 Directory Submission Plan
```bash
# Generate submission plan
python -m rankforge.main submit-plan example.com --name "My Business"
```

#### 🏷️ SEO Meta Tags
```bash
# Generate meta title + description
python -m rankforge.main meta "Keyword Research Tool" --summary "Free online keyword research tool"
```

#### ⚓ Anchor Text
```bash
# Generate anchor text suggestions
python -m rankforge.main anchors "https://mysite.com/blog/seo-guide" --context "SEO tips"
```

#### 🚀 Auto-Build (Full Pipeline)
```bash
# Run everything at once!
python -m rankforge.main auto-build example.com

# With keywords and specific provider
python -m rankforge.main auto-build example.com -k "seo tools,rank tracker" -p claude
```

#### 📂 View History
```bash
# See all stored data
python -m rankforge.main history

# Filter by category
python -m rankforge.main history --category keywords
```

#### 🗑️ Clear Cache
```bash
python -m rankforge.main clear-cache
```

---

## 📁 Project Structure

```
rankforge-cli/
├── rankforge/
│   ├── __init__.py              # Package root (version)
│   ├── main.py                  # CLI entry point (Typer commands)
│   │
│   ├── ai/                      # AI Provider Integrations
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract base + factory
│   │   ├── claude.py            # Anthropic Claude
│   │   ├── gpt.py               # OpenAI GPT
│   │   └── gemini.py            # Google Gemini
│   │
│   ├── seo/                     # SEO Analysis Tools
│   │   ├── __init__.py
│   │   ├── keywords.py          # Keyword research (Autocomplete + SerpAPI + AI)
│   │   ├── backlinks.py         # Backlink analysis (DataForSEO + AI)
│   │   ├── serp.py              # SERP analysis (SerpAPI + scraping)
│   │   ├── audit.py             # On-page SEO audit
│   │   └── competitors.py       # Competitor analysis
│   │
│   ├── automation/              # Off-Page SEO Automation
│   │   ├── __init__.py
│   │   ├── scraper.py           # Guest post finder + email extraction
│   │   ├── outreach.py          # AI outreach email generator
│   │   └── submission.py        # Directory submission planner
│   │
│   ├── utils/                   # Shared Utilities
│   │   ├── __init__.py
│   │   ├── logger.py            # Rich + file logging
│   │   ├── cache.py             # File-based JSON cache with TTL
│   │   ├── rate_limiter.py      # Token-bucket rate limiter
│   │   ├── display.py           # Rich tables, panels, spinners
│   │   └── export.py            # JSON/CSV export
│   │
│   ├── database/                # Storage Layer
│   │   ├── __init__.py
│   │   ├── memory.py            # JSON project memory
│   │   └── vector_store.py      # ChromaDB / JSON fallback
│   │
│   └── config/                  # Configuration
│       ├── __init__.py
│       └── settings.py          # Pydantic settings + .env loading
│
├── .env.example                 # Environment template
├── .gitignore
├── pyproject.toml               # Package config + CLI entry point
├── requirements.txt
└── README.md
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   CLI Layer (Typer)                  │
│  keyword │ backlinks │ serp │ audit │ ai │ outreach  │
└──────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │
┌──────▼──────────▼──────────▼──────────▼─────────────┐
│              Business Logic Modules                  │
│  seo/keywords │ seo/backlinks │ automation/outreach  │
└──────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │
┌──────▼──────────▼──────────▼──────────▼─────────────┐
│              Infrastructure Layer                    │
│  ai/base │ utils/cache │ utils/rate_limiter │ memory │
└─────────────────────────────────────────────────────┘
```

---

## 🧩 Extending RankForge

### Add a New AI Provider

1. Create `rankforge/ai/my_provider.py`
2. Extend `AIProvider` base class
3. Implement `generate_content()`
4. Register in `get_ai_provider()` factory in `base.py`

### Add a New SEO Module

1. Create `rankforge/seo/my_module.py`
2. Use `Cache`, `RateLimiter`, and `Display` utilities
3. Add a CLI command in `main.py`

---

## 📄 Sample Output

### Keyword Research
```
╔══════════════════════════════════════════════════╗
║  ⚒  RankForge CLI                               ║
║  v1.0.0  •  AI-Powered SEO Toolkit              ║
╚══════════════════════════════════════════════════╝

━━━ Keyword Research: 'seo services' ━━━

✔ Google Autocomplete: 8 suggestions
✔ AI generated 20 keyword ideas

┌──────────────────────────────────────────────────┐
│           Google Autocomplete Suggestions         │
├────┬─────────────────────────────────────────────┤
│  # │ Keyword Suggestion                          │
├────┼─────────────────────────────────────────────┤
│  1 │ seo services near me                        │
│  2 │ seo services pricing                        │
│  3 │ seo services for small business              │
│  4 │ seo services agency                          │
│  5 │ seo services company                         │
└────┴─────────────────────────────────────────────┘
```

### Site Audit
```
━━━ Site Audit: https://example.com ━━━

┌─────────────────────────────────────────────────┐
│                 Audit Summary                    │
├──────────────┬──────────────────────────────────┤
│ URL          │ https://example.com              │
│ Status Code  │ 200                              │
│ Overall Score│ 78/100                           │
└──────────────┴──────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              Category Scores                     │
├─────────────┬────────┬──────────────────────────┤
│ Category    │ Score  │ Issues                    │
├─────────────┼────────┼──────────────────────────┤
│ Meta Tags   │ 85/100 │ 1                        │
│ Headings    │ 75/100 │ 2                        │
│ Images      │ 70/100 │ 1                        │
│ Links       │ 90/100 │ 0                        │
│ Performance │ 70/100 │ 2                        │
└─────────────┴────────┴──────────────────────────┘
```

---

## ⚠️ Disclaimer

- This tool is intended for **legitimate SEO research and outreach**.
- The scraper respects `robots.txt` and implements rate limiting.
- Guest post finding and outreach are designed to assist — **not automate** — human-driven campaigns.
- No form auto-submission is performed without explicit user action.
- Always comply with the terms of service of third-party APIs and websites.

---

## 📜 License

MIT License — free for personal and commercial use.

---

<div align="center">

**Built with ❤️ for SEO professionals who love the terminal.**

</div>
