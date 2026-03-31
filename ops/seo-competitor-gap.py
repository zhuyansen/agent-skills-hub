#!/usr/bin/env python3
"""
SEO Competitor Gap Analysis for Agent Skills Hub

Compares agentskillshub.top against competitors by:
1. Fetching competitor sitemaps to discover their URL/page structure
2. Extracting keyword themes from competitor pages
3. Cross-referencing with our Supabase data (categories, scenarios, skills)
4. Identifying content gaps and coverage opportunities

FREE methods only — no paid API keys required.

Usage:
    python ops/seo-competitor-gap.py
    python ops/seo-competitor-gap.py --output ops/output/gap-report.md
    python ops/seo-competitor-gap.py --verbose

Requirements:
    pip install requests beautifulsoup4 supabase
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
OUR_DOMAIN = "agentskillshub.top"
OUR_SITE = f"https://{OUR_DOMAIN}"

COMPETITORS = {
    "toolify.ai": {
        "sitemap_urls": [
            "https://www.toolify.ai/sitemap.xml",
        ],
        "type": "ai-tool-directory",
        "description": "Large AI tool directory with categories and reviews",
    },
    "aitoolsdirectory.com": {
        "sitemap_urls": [
            "https://aitoolsdirectory.com/sitemap.xml",
        ],
        "type": "ai-tool-directory",
        "description": "AI tools directory with category pages",
    },
    "mcp.so": {
        "sitemap_urls": [
            "https://mcp.so/sitemap.xml",
        ],
        "type": "mcp-directory",
        "description": "MCP server directory — direct competitor for MCP category",
    },
    "glama.ai": {
        "sitemap_urls": [
            "https://glama.ai/sitemap.xml",
        ],
        "type": "mcp-directory",
        "description": "MCP server catalog with tool pages",
    },
}

# Supabase config (read from frontend/.env or environment)
SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY", "")

# Try loading from frontend/.env if not in environment
if not SUPABASE_URL:
    env_path = Path(__file__).resolve().parent.parent / "frontend" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("VITE_SUPABASE_URL="):
                SUPABASE_URL = line.split("=", 1)[1].strip()
            elif line.startswith("VITE_SUPABASE_ANON_KEY="):
                SUPABASE_ANON_KEY = line.split("=", 1)[1].strip()

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", str(Path(__file__).resolve().parent / "output")))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VERBOSE = False

# ─────────────────────────────────────────────
# Our known categories and scenarios
# ─────────────────────────────────────────────
OUR_CATEGORIES = {
    "agent-tool": "Agent Frameworks & Tools",
    "mcp-server": "MCP Servers",
    "claude-skill": "Claude Code Skills",
    "codex-skill": "Codex Skills",
}

OUR_SCENARIOS = [
    "web-scraping", "mcp-database", "mcp-browser", "code-review",
    "code-completion", "workflow-automation", "claude-code-skills",
    "security-audit", "prompt-engineering", "semantic-search",
    "ci-cd", "browser-automation", "git-tools", "slack-integration",
    "content-writing", "debugging",
    # Extended list (53 total on site)
    "api-integration", "data-pipeline", "llm-orchestration",
    "rag-retrieval", "vector-database", "local-ai", "multi-agent",
    "memory-management", "file-system", "docker-kubernetes",
    "testing-qa", "documentation", "image-generation",
    "voice-audio", "email-automation", "calendar-scheduling",
    "project-management", "note-taking", "pdf-processing",
    "spreadsheet", "translation", "summarization",
    "chatbot-building", "monitoring-observability", "log-analysis",
    "auth-security", "rate-limiting", "caching", "search-engine",
    "notification", "payment-billing", "crm-integration",
    "social-media", "seo-tools", "analytics", "deployment",
    "infrastructure", "cost-optimization",
]

# Keywords we want to rank for (derived from our content verticals)
TARGET_KEYWORDS = {
    # High priority — our core identity
    "high": [
        "ai agent tools", "ai agent framework", "mcp server",
        "claude code skills", "ai coding agent", "agent skills",
        "model context protocol", "best ai agent", "ai agent directory",
        "ai agent catalog", "mcp server list", "claude skills",
        "ai developer tools", "agent orchestration", "multi agent framework",
    ],
    # Medium priority — use-case keywords
    "medium": [
        "ai web scraping", "ai code review", "ai workflow automation",
        "ai browser automation", "ai security audit", "ai semantic search",
        "best mcp servers", "claude code extensions", "ai agent comparison",
        "ai tool comparison", "open source ai agents", "ai agent github",
        "mcp server database", "mcp server browser", "ai debugging tools",
        "ai content writing tools", "ai git tools", "ai ci cd",
    ],
    # Long-tail — scenario-specific
    "long_tail": [
        "best ai agent for web scraping",
        "best mcp server for database",
        "claude code skill for coding",
        "ai agent vs ai tool",
        "how to build ai agent",
        "mcp server tutorial",
        "ai agent for devops",
        "open source mcp server",
        "ai agent framework comparison 2026",
        "best ai tools for developers",
        "ai agent for api integration",
        "ai agent for data pipeline",
    ],
}


# ─────────────────────────────────────────────
# Sitemap Fetching
# ─────────────────────────────────────────────

def fetch_sitemap(url, depth=0, max_depth=2):
    """Fetch and parse a sitemap XML, following sitemap indexes recursively."""
    if depth > max_depth:
        return []

    urls = []
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AgentSkillsHub-SEOBot/1.0)",
        })
        with urllib.request.urlopen(req, timeout=20) as response:
            data = response.read().decode("utf-8", errors="ignore")

        # Strip namespace for easier parsing
        data = re.sub(r'\s+xmlns\s*=\s*"[^"]*"', '', data, count=1)
        root = ET.fromstring(data)

        # Check if it's a sitemap index
        sitemaps = root.findall(".//sitemap")
        if sitemaps:
            for sm in sitemaps:
                loc = sm.find("loc")
                if loc is not None and loc.text:
                    if VERBOSE:
                        print(f"    Following sitemap index: {loc.text}")
                    urls.extend(fetch_sitemap(loc.text.strip(), depth + 1, max_depth))
            return urls

        # Regular sitemap — extract URLs
        for url_elem in root.findall(".//url"):
            loc = url_elem.find("loc")
            if loc is not None and loc.text:
                urls.append(loc.text.strip())

    except Exception as e:
        if VERBOSE:
            print(f"    Warning: Failed to fetch {url}: {e}")

    return urls


def fetch_competitor_sitemaps():
    """Fetch sitemaps for all competitors."""
    results = {}
    for domain, config in COMPETITORS.items():
        print(f"  Fetching sitemap for {domain}...")
        all_urls = []
        for sitemap_url in config["sitemap_urls"]:
            urls = fetch_sitemap(sitemap_url)
            all_urls.extend(urls)
            time.sleep(0.5)  # Be polite

        results[domain] = {
            "urls": all_urls,
            "count": len(all_urls),
            "type": config["type"],
            "description": config["description"],
        }
        print(f"    Found {len(all_urls)} URLs")

    return results


# ─────────────────────────────────────────────
# URL Analysis
# ─────────────────────────────────────────────

def extract_keywords_from_urls(urls):
    """Extract keyword themes from URL paths."""
    keywords = Counter()
    categories = Counter()
    tool_names = set()
    page_types = Counter()

    for url in urls:
        parsed = urlparse(url)
        path = unquote(parsed.path).strip("/")
        parts = path.split("/")

        if not parts or not parts[0]:
            continue

        # Classify page type
        if len(parts) == 1:
            page_types["top-level"] += 1
        elif parts[0] in ("category", "categories", "cat", "c"):
            page_types["category"] += 1
            if len(parts) > 1:
                categories[parts[1]] += 1
        elif parts[0] in ("tool", "tools", "ai", "server", "servers", "skill", "skills"):
            page_types["tool-detail"] += 1
            if len(parts) > 1:
                tool_names.add(parts[-1])
        elif parts[0] in ("best", "top", "compare", "comparison", "vs", "alternative", "alternatives"):
            page_types["comparison-listicle"] += 1
        elif parts[0] in ("blog", "post", "article", "guide", "guides"):
            page_types["blog-content"] += 1
        else:
            page_types["other"] += 1

        # Extract keywords from path segments
        for part in parts:
            # Split on hyphens and underscores
            words = re.split(r'[-_]', part.lower())
            for word in words:
                word = word.strip()
                if len(word) > 2 and not word.isdigit():
                    keywords[word] += 1

    return {
        "keywords": keywords,
        "categories": categories,
        "tool_names": tool_names,
        "page_types": page_types,
    }


def analyze_competitor_themes(competitor_data):
    """Analyze what themes/categories each competitor covers."""
    analyses = {}

    for domain, data in competitor_data.items():
        urls = data["urls"]
        if not urls:
            analyses[domain] = {"error": "No URLs found"}
            continue

        analysis = extract_keywords_from_urls(urls)

        # Find AI/agent-related keywords
        ai_keywords = Counter()
        for kw, count in analysis["keywords"].items():
            if any(term in kw for term in [
                "ai", "agent", "mcp", "llm", "gpt", "claude", "openai",
                "automation", "tool", "api", "code", "dev", "data",
                "search", "browser", "security", "workflow", "chat",
                "bot", "model", "prompt", "rag", "vector", "embed",
                "server", "skill", "plugin", "extension",
            ]):
                ai_keywords[kw] = count

        analyses[domain] = {
            "total_urls": len(urls),
            "page_types": dict(analysis["page_types"]),
            "top_keywords": analysis["keywords"].most_common(50),
            "ai_keywords": ai_keywords.most_common(30),
            "categories": analysis["categories"].most_common(20),
            "tool_count": len(analysis["tool_names"]),
            "sample_tools": list(analysis["tool_names"])[:20],
        }

    return analyses


# ─────────────────────────────────────────────
# Supabase Data
# ─────────────────────────────────────────────

def fetch_our_data():
    """Fetch our skill data from Supabase for cross-reference."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("  Warning: No Supabase credentials. Skipping DB cross-reference.")
        return None

    import urllib.request
    import json

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    }

    data = {
        "categories": Counter(),
        "total_skills": 0,
        "top_skills": [],
        "topics": Counter(),
        "languages": Counter(),
    }

    try:
        # Fetch category distribution
        url = f"{SUPABASE_URL}/rest/v1/skills?select=category,stars,repo_full_name,description,topics&order=stars.desc&limit=5000"
        req = urllib.request.Request(url, headers={
            **headers,
            "Accept": "application/json",
            "Prefer": "count=exact",
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            skills = json.loads(response.read().decode("utf-8"))
            count_header = response.headers.get("Content-Range", "")

        data["total_skills"] = len(skills)
        if count_header and "/" in count_header:
            try:
                data["total_skills"] = int(count_header.split("/")[1])
            except (ValueError, IndexError):
                pass

        for skill in skills:
            cat = skill.get("category", "unknown")
            data["categories"][cat] += 1

            # Extract topics
            topics = skill.get("topics")
            if topics:
                try:
                    topic_list = json.loads(topics) if isinstance(topics, str) else topics
                    for t in topic_list:
                        data["topics"][t] += 1
                except (json.JSONDecodeError, TypeError):
                    pass

        data["top_skills"] = [
            {
                "name": s.get("repo_full_name", ""),
                "stars": s.get("stars", 0),
                "category": s.get("category", ""),
                "description": (s.get("description") or "")[:100],
            }
            for s in skills[:50]
        ]

        print(f"  Fetched {data['total_skills']} skills from Supabase")
        print(f"  Categories: {dict(data['categories'].most_common(10))}")

    except Exception as e:
        print(f"  Warning: Supabase fetch error: {e}")
        return None

    return data


# ─────────────────────────────────────────────
# Gap Analysis
# ─────────────────────────────────────────────

def compute_gaps(competitor_analyses, our_data):
    """Identify gaps between our coverage and competitors."""
    gaps = {
        "missing_categories": [],
        "thin_categories": [],
        "missing_page_types": [],
        "keyword_opportunities": [],
        "competitor_advantages": [],
        "our_advantages": [],
    }

    # Aggregate all competitor keywords
    all_competitor_keywords = Counter()
    for domain, analysis in competitor_analyses.items():
        if "error" in analysis:
            continue
        for kw, count in analysis.get("ai_keywords", []):
            all_competitor_keywords[kw] += count

    # Keywords competitors use heavily that we should target
    our_url_keywords = set()
    for scenario in OUR_SCENARIOS:
        for word in scenario.split("-"):
            our_url_keywords.add(word)
    for cat in OUR_CATEGORIES:
        for word in cat.split("-"):
            our_url_keywords.add(word)

    for kw, count in all_competitor_keywords.most_common(100):
        if kw not in our_url_keywords and count >= 3:
            gaps["keyword_opportunities"].append({
                "keyword": kw,
                "competitor_mentions": count,
                "action": f"Consider adding '{kw}' themed scenario or category page",
            })

    # Page type gaps
    our_page_types = {"tool-detail", "category", "comparison-listicle", "top-level"}
    for domain, analysis in competitor_analyses.items():
        if "error" in analysis:
            continue
        for ptype, count in analysis.get("page_types", {}).items():
            if ptype == "blog-content" and count > 20:
                gaps["missing_page_types"].append({
                    "type": "blog-content",
                    "competitor": domain,
                    "count": count,
                    "action": "Consider adding blog/guide content for SEO",
                })
            if ptype == "comparison-listicle" and count > 5:
                gaps["missing_page_types"].append({
                    "type": "comparison-listicle",
                    "competitor": domain,
                    "count": count,
                    "action": "Add more 'best X for Y' / comparison pages",
                })

    # Competitor size advantage
    for domain, analysis in competitor_analyses.items():
        if "error" in analysis:
            continue
        total = analysis.get("total_urls", 0)
        tool_count = analysis.get("tool_count", 0)
        our_total = our_data["total_skills"] if our_data else 0

        if tool_count > 0:
            if tool_count > our_total * 1.5:
                gaps["competitor_advantages"].append({
                    "competitor": domain,
                    "their_tools": tool_count,
                    "our_skills": our_total,
                    "insight": f"{domain} has ~{tool_count} tool pages vs our ~{our_total}",
                })
            elif our_total > tool_count * 1.5:
                gaps["our_advantages"].append({
                    "competitor": domain,
                    "their_tools": tool_count,
                    "our_skills": our_total,
                    "insight": f"We have ~{our_total} skills vs {domain}'s ~{tool_count}",
                })

    # Check if competitors have categories we don't
    competitor_categories = set()
    for domain, analysis in competitor_analyses.items():
        if "error" in analysis:
            continue
        for cat, _ in analysis.get("categories", []):
            competitor_categories.add(cat.lower())

    # Cross-reference with our topic coverage
    if our_data:
        our_topics = set(t.lower() for t in our_data["topics"].keys())
        for comp_cat in sorted(competitor_categories):
            # Check if any of our topics cover this
            if not any(comp_cat in topic or topic in comp_cat for topic in our_topics):
                if len(comp_cat) > 2:
                    gaps["missing_categories"].append({
                        "category": comp_cat,
                        "action": f"Competitors have '{comp_cat}' category — evaluate if relevant",
                    })

    return gaps


# ─────────────────────────────────────────────
# Keyword Coverage Check (free, using site: queries)
# ─────────────────────────────────────────────

def check_our_indexing():
    """Check how many of our pages Google has indexed using site: estimate."""
    print("  Checking our sitemap for page count...")
    our_urls = fetch_sitemap(f"{OUR_SITE}/sitemap.xml")

    page_types = Counter()
    for url in our_urls:
        path = urlparse(url).path.strip("/")
        parts = path.split("/")
        if not parts or not parts[0]:
            page_types["homepage"] += 1
        elif parts[0] == "skill":
            page_types["skill-detail"] += 1
        elif parts[0] == "category":
            page_types["category"] += 1
        elif parts[0] == "best":
            page_types["scenario"] += 1
        elif parts[0] == "compare":
            page_types["compare"] += 1
        else:
            page_types["other"] += 1

    return {
        "total_sitemap_urls": len(our_urls),
        "page_types": dict(page_types),
    }


# ─────────────────────────────────────────────
# Report Generation
# ─────────────────────────────────────────────

def generate_report(competitor_analyses, our_data, gaps, our_indexing, output_path):
    """Generate a markdown gap analysis report."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []

    lines.append(f"# SEO Competitor Gap Analysis — {today}")
    lines.append(f"**Site:** {OUR_DOMAIN}")
    lines.append(f"**Competitors:** {', '.join(COMPETITORS.keys())}")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    if our_data:
        lines.append(f"- **Our skills indexed:** {our_data['total_skills']}")
        lines.append(f"- **Our categories:** {len(our_data['categories'])} ({', '.join(c for c, _ in our_data['categories'].most_common(5))})")
        lines.append(f"- **Our scenarios:** {len(OUR_SCENARIOS)} scenario pages")
    if our_indexing:
        lines.append(f"- **Our sitemap URLs:** {our_indexing['total_sitemap_urls']}")
        for ptype, count in sorted(our_indexing["page_types"].items(), key=lambda x: -x[1]):
            lines.append(f"  - {ptype}: {count}")
    lines.append("")

    # Competitor Overview
    lines.append("## Competitor Overview")
    lines.append("")
    lines.append("| Competitor | Type | Total URLs | Tool Pages | Top Keywords |")
    lines.append("|---|---|---|---|---|")
    for domain, analysis in competitor_analyses.items():
        if "error" in analysis:
            lines.append(f"| {domain} | {COMPETITORS[domain]['type']} | Error | - | - |")
            continue
        top_kw = ", ".join(kw for kw, _ in analysis.get("ai_keywords", [])[:5])
        lines.append(
            f"| {domain} | {COMPETITORS[domain]['type']} | "
            f"{analysis['total_urls']} | ~{analysis['tool_count']} | {top_kw} |"
        )
    lines.append("")

    # Detailed Competitor Analysis
    for domain, analysis in competitor_analyses.items():
        if "error" in analysis:
            continue
        lines.append(f"### {domain}")
        lines.append(f"*{COMPETITORS[domain]['description']}*")
        lines.append("")
        lines.append(f"- **Total indexed URLs:** {analysis['total_urls']}")
        lines.append(f"- **Estimated tool pages:** ~{analysis['tool_count']}")
        lines.append(f"- **Page type distribution:** {json.dumps(analysis['page_types'])}")
        lines.append("")

        if analysis.get("categories"):
            lines.append("**Their categories:**")
            for cat, count in analysis["categories"][:15]:
                lines.append(f"  - {cat} ({count} pages)")
            lines.append("")

        if analysis.get("sample_tools"):
            lines.append(f"**Sample tools (from URLs):** {', '.join(analysis['sample_tools'][:10])}")
            lines.append("")

    # Gap Analysis
    lines.append("## Gap Analysis")
    lines.append("")

    # Keyword opportunities
    kw_opps = gaps.get("keyword_opportunities", [])
    if kw_opps:
        lines.append("### Keyword Opportunities")
        lines.append("Keywords competitors target heavily that we should consider:")
        lines.append("")
        lines.append("| Keyword | Competitor Mentions | Suggested Action |")
        lines.append("|---|---|---|")
        for opp in kw_opps[:25]:
            lines.append(f"| {opp['keyword']} | {opp['competitor_mentions']} | {opp['action']} |")
        lines.append("")

    # Missing page types
    missing_types = gaps.get("missing_page_types", [])
    if missing_types:
        lines.append("### Missing Page Types")
        lines.append("")
        for mt in missing_types:
            lines.append(f"- **{mt['type']}**: {mt['competitor']} has {mt['count']} pages. {mt['action']}")
        lines.append("")

    # Competitor advantages
    comp_advs = gaps.get("competitor_advantages", [])
    if comp_advs:
        lines.append("### Competitor Size Advantages")
        lines.append("")
        for ca in comp_advs:
            lines.append(f"- {ca['insight']}")
        lines.append("")

    # Our advantages
    our_advs = gaps.get("our_advantages", [])
    if our_advs:
        lines.append("### Our Advantages")
        lines.append("")
        for oa in our_advs:
            lines.append(f"- {oa['insight']}")
        lines.append("")

    # Actionable Recommendations
    lines.append("## Actionable Recommendations")
    lines.append("")
    lines.append("### Priority 1: Quick Wins (1-2 weeks)")
    lines.append("")
    lines.append("1. **Optimize existing scenario pages** for target keywords")
    lines.append("   - Ensure each `/best/{scenario}/` page has unique title tags, H1, meta description")
    lines.append("   - Add structured data (FAQ schema, ItemList schema) to scenario pages")
    lines.append("2. **Add internal linking** between related skills and scenario pages")
    lines.append("3. **Improve page titles** to include 'best', 'top', '2026' for freshness signals")
    lines.append("")

    lines.append("### Priority 2: Content Expansion (2-4 weeks)")
    lines.append("")
    lines.append("1. **Create comparison pages**: `/compare/{tool-a}-vs-{tool-b}/`")
    lines.append("   - Focus on high-star skills in the same subcategory")
    lines.append("2. **Add 'alternatives to' pages**: `/best/alternatives-to-{popular-tool}/`")
    lines.append("3. **Create 'how to' guides**: integrate with scenario pages")
    lines.append("   - 'How to set up an MCP server for databases'")
    lines.append("   - 'Best AI agents for web scraping in 2026'")
    lines.append("")

    lines.append("### Priority 3: Strategic (1-3 months)")
    lines.append("")
    lines.append("1. **Blog/content section** for long-form SEO")
    if kw_opps:
        top_kw_str = ", ".join(o["keyword"] for o in kw_opps[:5])
        lines.append(f"2. **Target competitor keyword gaps**: {top_kw_str}")
    lines.append("3. **Build topical authority** by creating hub pages for each major category")
    lines.append("4. **Schema markup**: Add SoftwareApplication, Article, BreadcrumbList schemas")
    lines.append("")

    # Target keyword checklist
    lines.append("## Target Keyword Checklist")
    lines.append("")
    for priority, keywords in TARGET_KEYWORDS.items():
        lines.append(f"### {priority.replace('_', ' ').title()} Priority")
        lines.append("")
        for kw in keywords:
            lines.append(f"- [ ] `{kw}`")
        lines.append("")

    # Write report
    report_text = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(report_text)

    # Also save raw JSON data
    json_path = output_path.with_suffix(".json")
    raw_data = {
        "date": today,
        "our_domain": OUR_DOMAIN,
        "our_data": {
            "total_skills": our_data["total_skills"] if our_data else 0,
            "categories": dict(our_data["categories"]) if our_data else {},
            "top_topics": dict(our_data["topics"].most_common(50)) if our_data else {},
        } if our_data else None,
        "our_indexing": our_indexing,
        "competitor_analyses": {
            domain: {
                k: v for k, v in analysis.items()
                if k != "tool_names"  # set not JSON serializable
            }
            for domain, analysis in competitor_analyses.items()
        },
        "gaps": gaps,
        "target_keywords": TARGET_KEYWORDS,
    }
    with open(json_path, "w") as f:
        json.dump(raw_data, f, indent=2, default=str)

    return report_text


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    global VERBOSE

    parser = argparse.ArgumentParser(description="SEO Competitor Gap Analysis for Agent Skills Hub")
    parser.add_argument("--output", "-o", default=str(OUTPUT_DIR / "seo-gap-report.md"),
                        help="Output report path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--skip-supabase", action="store_true", help="Skip Supabase data fetch")
    parser.add_argument("--skip-competitors", action="store_true", help="Skip competitor sitemap fetch")
    args = parser.parse_args()

    VERBOSE = args.verbose
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== SEO Competitor Gap Analysis ===")
    print(f"Our site: {OUR_DOMAIN}")
    print(f"Competitors: {', '.join(COMPETITORS.keys())}")
    print()

    # Step 1: Fetch competitor sitemaps
    if args.skip_competitors:
        print("[1/4] Skipping competitor sitemap fetch")
        competitor_data = {}
    else:
        print("[1/4] Fetching competitor sitemaps...")
        competitor_data = fetch_competitor_sitemaps()
    print()

    # Step 2: Analyze competitor themes
    print("[2/4] Analyzing competitor page structures...")
    competitor_analyses = analyze_competitor_themes(competitor_data)
    for domain, analysis in competitor_analyses.items():
        if "error" not in analysis:
            print(f"  {domain}: {analysis['total_urls']} URLs, ~{analysis['tool_count']} tools")
    print()

    # Step 3: Fetch our data
    if args.skip_supabase:
        print("[3/4] Skipping Supabase data fetch")
        our_data = None
    else:
        print("[3/4] Fetching our data from Supabase...")
        our_data = fetch_our_data()
    print()

    # Step 3.5: Check our indexing
    print("[3.5/4] Checking our sitemap...")
    our_indexing = check_our_indexing()
    print(f"  Our sitemap: {our_indexing['total_sitemap_urls']} URLs")
    print()

    # Step 4: Compute gaps
    print("[4/4] Computing gap analysis...")
    gaps = compute_gaps(competitor_analyses, our_data)
    kw_gaps = len(gaps.get("keyword_opportunities", []))
    print(f"  Found {kw_gaps} keyword opportunities")
    print(f"  Found {len(gaps.get('missing_page_types', []))} missing page types")
    print(f"  Found {len(gaps.get('competitor_advantages', []))} competitor advantages")
    print(f"  Found {len(gaps.get('our_advantages', []))} our advantages")
    print()

    # Generate report
    print(f"Generating report to {output_path}...")
    report = generate_report(competitor_analyses, our_data, gaps, our_indexing, output_path)
    print(f"Report saved to {output_path}")
    print(f"Raw data saved to {output_path.with_suffix('.json')}")
    print()

    # Print executive summary
    print("=== Quick Summary ===")
    for domain, analysis in competitor_analyses.items():
        if "error" not in analysis:
            print(f"  {domain}: {analysis['total_urls']} pages, top keywords: "
                  f"{', '.join(kw for kw, _ in analysis.get('ai_keywords', [])[:3])}")
    if our_data:
        print(f"  Us ({OUR_DOMAIN}): {our_data['total_skills']} skills across "
              f"{len(our_data['categories'])} categories")

    return 0


if __name__ == "__main__":
    sys.exit(main())
