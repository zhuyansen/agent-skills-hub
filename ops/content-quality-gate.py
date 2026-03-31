#!/usr/bin/env python3
"""
Content Quality Gate for Agent Skills Hub daily/weekly reports.

Scores markdown content on 5 dimensions (100 points total):
  - Specificity (0-20): tool names, star counts, concrete numbers
  - AI Detection (0-20): penalty for AI-typical phrases
  - Engagement (0-20): hooks, questions, emojis, call-to-action
  - Freshness (0-20): date references, "new"/"trending" language, recency signals
  - Completeness (0-20): required sections (title, intro, top 10, links, CTA)

Verdict: PASS (80+) | REVIEW (60-79) | FAIL (<60)

Inspired by ericosiu/ai-marketing-skills content-ops quality scorer,
adapted for Agent Skills Hub's Chinese/English bilingual reports.

Usage:
    python ops/content-quality-gate.py path/to/report.md
    python ops/content-quality-gate.py path/to/report.md --verbose
    python ops/content-quality-gate.py path/to/report.md --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


# ============================================================
# Configuration
# ============================================================

# AI slop words/phrases (English + Chinese equivalents)
AI_SLOP_PHRASES = [
    # English AI cliches
    "delve", "comprehensive", "robust", "leverage", "utilize",
    "seamless", "cutting-edge", "groundbreaking", "innovative",
    "transformative", "paradigm", "holistic", "synergy",
    "ecosystem", "landscape", "multifaceted", "nuanced",
    "pivotal", "testament", "realm", "intricate",
    "meticulous", "paramount", "fostering", "garner",
    "underscore", "commendable", "tapestry", "embark",
    "game-changer", "unlock the power", "dive into",
    "at the end of the day", "it is important to note",
    "I'm excited to share", "stay tuned",
    # Chinese AI cliches
    "赋能", "全方位", "一站式", "颠覆性", "无缝衔接",
    "深度赋能", "全面赋能", "助力", "引领", "打造",
    "生态闭环", "底层逻辑", "顶层设计",
]

# AI writing patterns (regex)
AI_PATTERNS = [
    (r"(?:is|stands as|serves as) a testament", "significance inflation"),
    (r"it'?s not just .{1,40}, it'?s", "negative parallelism"),
    (r"(?:experts|studies|reports) (?:believe|show|suggest)", "vague attribution"),
    (r"the future (?:looks|is) bright", "generic conclusion"),
    (r"in today'?s (?:rapidly|ever|fast)", "cliche opener"),
    (r"不仅仅是.{1,20}更是", "Chinese negative parallelism"),
    (r"在当今.{1,15}时代", "Chinese cliche opener"),
    (r"值得一提的是", "Chinese filler"),
]

# Engagement signals
ENGAGEMENT_PATTERNS_EN = [
    r"\?",                              # questions
    r"[\U0001F300-\U0001F9FF]",         # emoji
    r"(?:check it out|try it|star it|explore|subscribe)",
    r"(?:what do you think|thoughts\?|agree\?)",
    r"(?:Top \d+|#\d+)",               # numbered lists
    r"(?:https?://\S+)",               # links
]

ENGAGEMENT_PATTERNS_ZH = [
    r"[？]",                            # Chinese question mark
    r"[\U0001F300-\U0001F9FF]",         # emoji
    r"(?:快来|试试|一起|关注|收藏|点赞|转发)",
    r"(?:你怎么看|你觉得|有没有)",
    r"(?:Top \d+|第\d+名|排名)",
    r"(?:https?://\S+)",
]

# Required sections for daily report
DAILY_REPORT_SECTIONS = [
    ("title", r"(?:^#\s|日报|Daily|Top\s*\d+|精选|今[日天])", "Title/heading"),
    ("intro", r"(?:^.{20,})", "Introduction paragraph (20+ chars)"),
    ("tool_list", r"(?:\d+[\.\)、]|\*\*\d+)", "Numbered tool list"),
    ("links", r"(?:https?://|github\.com/|agentskillshub)", "Links/URLs"),
    ("cta", r"(?:关注|订阅|Explore|Subscribe|Star|收藏|Check|查看|访问)", "Call-to-action"),
]

# Required sections for weekly newsletter
WEEKLY_REPORT_SECTIONS = [
    ("title", r"(?:^#\s|周报|Weekly|Newsletter|New This Week|Trending)", "Title/heading"),
    ("intro", r"(?:^.{20,})", "Introduction paragraph"),
    ("new_skills", r"(?:New|新[增上]|本周|This Week)", "New skills section"),
    ("trending", r"(?:Trending|趋势|热门|增速|velocity|Still Trending)", "Trending section"),
    ("links", r"(?:https?://|github\.com/|agentskillshub)", "Links/URLs"),
    ("cta", r"(?:关注|订阅|Explore|Subscribe|Star|收藏)", "Call-to-action"),
]

# Freshness date patterns
DATE_PATTERNS = [
    r"\d{4}-\d{2}-\d{2}",             # 2026-03-31
    r"\d{1,2}月\d{1,2}[日号]",         # 3月31日
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}",
    r"(?:今[日天]|昨[日天]|本周|上周|最近|近期|过去\d+[天小时])",
    r"(?:today|yesterday|this week|last week|recent|past \d+ (?:days?|hours?))",
]


# ============================================================
# Scoring functions
# ============================================================

@dataclass
class DimensionResult:
    name: str
    score: float = 0.0     # 0-20
    max_score: float = 20.0
    details: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)


def score_specificity(text: str) -> DimensionResult:
    """Does the report mention specific tool names, star counts, numbers?"""
    result = DimensionResult(name="Specificity")
    score = 0.0

    # GitHub-style repo names (owner/repo)
    repos = re.findall(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", text)
    repo_count = len(set(repos))
    if repo_count >= 10:
        score += 6.0
        result.details.append(f"Found {repo_count} repo references (excellent)")
    elif repo_count >= 5:
        score += 4.0
        result.details.append(f"Found {repo_count} repo references (good)")
    elif repo_count >= 1:
        score += 2.0
        result.details.append(f"Found {repo_count} repo references (needs more)")
    else:
        result.penalties.append("No repo names (owner/repo format) found")

    # Star counts and numeric data
    star_patterns = re.findall(
        r"(?:\d[\d,]*\s*(?:stars?|Stars?|[⭐★])|[⭐★]\s*\d[\d,]*)", text
    )
    number_patterns = re.findall(
        r"\d[\d,]*(?:\.\d+)?(?:\s*[KkMm]\b|\s*%|\s*x\b)", text
    )
    plain_numbers = re.findall(r"\b\d{2,}\b", text)

    num_count = len(star_patterns) + len(number_patterns)
    if num_count >= 10:
        score += 6.0
        result.details.append(f"Found {num_count} specific numbers/star counts (excellent)")
    elif num_count >= 5:
        score += 4.0
        result.details.append(f"Found {num_count} specific numbers/star counts (good)")
    elif num_count >= 1:
        score += 2.0
        result.details.append(f"Found {num_count} specific numbers/star counts (needs more)")
    else:
        result.penalties.append("No star counts or specific numbers found")

    # Category/tag mentions
    categories = re.findall(
        r"(?:coding|agent|automation|mcp|rag|chatbot|devops|testing|security|"
        r"编码|智能体|自动化|开发|测试|安全|部署|框架|工具)",
        text, re.IGNORECASE,
    )
    if len(categories) >= 3:
        score += 4.0
        result.details.append(f"Found {len(categories)} category references")
    elif len(categories) >= 1:
        score += 2.0
        result.details.append(f"Found {len(categories)} category references (could use more)")
    else:
        result.penalties.append("No category/domain tags found")

    # Descriptions with concrete details (sentences with both a name and a verb)
    descriptive = re.findall(
        r"[A-Za-z0-9_-]+/[A-Za-z0-9_-]+.{5,80}(?:支持|实现|提供|enables?|provides?|supports?|automat)",
        text, re.IGNORECASE,
    )
    if len(descriptive) >= 3:
        score += 4.0
        result.details.append(f"Found {len(descriptive)} descriptive tool entries")
    elif len(descriptive) >= 1:
        score += 2.0
        result.details.append(f"Found {len(descriptive)} descriptive entries (add more detail)")

    result.score = min(score, 20.0)
    return result


def score_ai_detection(text: str) -> DimensionResult:
    """Penalty-based: starts at 20, loses points for AI-typical phrases."""
    result = DimensionResult(name="AI Detection")
    score = 20.0

    text_lower = text.lower()

    # Check banned phrases
    found_phrases = []
    for phrase in AI_SLOP_PHRASES:
        if phrase.lower() in text_lower:
            found_phrases.append(phrase)

    if found_phrases:
        penalty = min(len(found_phrases) * 2.0, 12.0)
        score -= penalty
        shown = found_phrases[:5]
        remaining = len(found_phrases) - len(shown)
        msg = f"AI slop phrases found: {', '.join(shown)}"
        if remaining > 0:
            msg += f" (+{remaining} more)"
        result.penalties.append(msg)
    else:
        result.details.append("No AI slop phrases detected")

    # Check AI patterns
    found_patterns = []
    for pattern, label in AI_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            found_patterns.append(label)

    if found_patterns:
        penalty = min(len(found_patterns) * 2.0, 8.0)
        score -= penalty
        result.penalties.append(f"AI writing patterns: {', '.join(found_patterns)}")
    else:
        result.details.append("No AI writing patterns detected")

    # Em dash overuse (common AI tell)
    em_dash_count = text.count("\u2014") + text.count("--")
    word_count = max(len(text.split()), 1)
    if em_dash_count > word_count / 50:
        score -= 2.0
        result.penalties.append(f"Excessive em dashes: {em_dash_count} in {word_count} words")

    # Repetitive sentence starters
    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("#")]
    if len(lines) >= 5:
        starters = [l[:15] for l in lines]
        from collections import Counter
        starter_counts = Counter(starters)
        repetitive = [s for s, c in starter_counts.items() if c >= 3]
        if repetitive:
            score -= 2.0
            result.penalties.append("Repetitive sentence starters detected")

    result.score = max(score, 0.0)
    return result


def score_engagement(text: str) -> DimensionResult:
    """Hooks, questions, emojis, call-to-action."""
    result = DimensionResult(name="Engagement")
    score = 0.0

    # Detect language mix
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", text))
    patterns = ENGAGEMENT_PATTERNS_ZH if has_chinese else ENGAGEMENT_PATTERNS_EN

    # Questions
    q_count = len(re.findall(r"[?？]", text))
    if q_count >= 2:
        score += 4.0
        result.details.append(f"Found {q_count} questions (good engagement)")
    elif q_count >= 1:
        score += 2.0
        result.details.append(f"Found {q_count} question")
    else:
        result.penalties.append("No questions found -- consider adding one to invite discussion")

    # Emojis
    emoji_count = len(re.findall(r"[\U0001F300-\U0001F9FF\U00002702-\U000027B0\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]", text))
    if emoji_count >= 5:
        score += 4.0
        result.details.append(f"Good emoji usage ({emoji_count} emojis)")
    elif emoji_count >= 2:
        score += 3.0
        result.details.append(f"Some emoji usage ({emoji_count})")
    elif emoji_count >= 1:
        score += 1.0
        result.details.append(f"Minimal emoji ({emoji_count})")
    else:
        result.penalties.append("No emojis -- social content benefits from visual markers")

    # Call-to-action
    cta_patterns = [
        r"(?:关注|订阅|收藏|点赞|转发|Star|subscribe|follow|check.?out|explore|try)",
        r"(?:agentskillshub\.top|github\.com)",
        r"(?:链接|link|URL|详情|了解更多|read more|learn more)",
    ]
    cta_found = 0
    for pat in cta_patterns:
        if re.search(pat, text, re.IGNORECASE):
            cta_found += 1
    if cta_found >= 2:
        score += 4.0
        result.details.append("Strong call-to-action presence")
    elif cta_found >= 1:
        score += 2.0
        result.details.append("Basic call-to-action found")
    else:
        result.penalties.append("No call-to-action found")

    # Hook in first 200 chars
    hook_text = text[:200]
    hook_signals = [
        r"(?:Top \d+|精选|今[日天]|本周|Breaking|Hot|Fire|New)",
        r"[\U0001F525\U0001F680\U00002B50\U0001F4A5\U0001F31F]",  # fire, rocket, star emojis
        r"\d+",  # numbers in hook
        r"[!！]",  # exclamation
    ]
    hook_score = sum(1 for pat in hook_signals if re.search(pat, hook_text, re.IGNORECASE))
    if hook_score >= 3:
        score += 4.0
        result.details.append("Strong opening hook")
    elif hook_score >= 2:
        score += 3.0
        result.details.append("Decent opening hook")
    elif hook_score >= 1:
        score += 1.0
        result.details.append("Weak opening hook")
    else:
        result.penalties.append("Opening lacks a hook -- add numbers, emojis, or urgency")

    # Numbered/ranked list (engagement-friendly format)
    numbered = re.findall(r"(?:^|\n)\s*(?:\d+[\.\)、]|[#＃]\d+)", text)
    if len(numbered) >= 5:
        score += 4.0
        result.details.append(f"Well-structured numbered list ({len(numbered)} items)")
    elif len(numbered) >= 1:
        score += 2.0
        result.details.append(f"Has numbered items ({len(numbered)})")

    result.score = min(score, 20.0)
    return result


def score_freshness(text: str) -> DimensionResult:
    """Are the mentioned tools actually new/trending? Cross-check with date refs."""
    result = DimensionResult(name="Freshness")
    score = 0.0

    today = datetime.now()

    # Date references in text
    date_refs = []
    for pat in DATE_PATTERNS:
        matches = re.findall(pat, text, re.IGNORECASE)
        date_refs.extend(matches)

    if len(date_refs) >= 3:
        score += 6.0
        result.details.append(f"Found {len(date_refs)} date/time references (timely)")
    elif len(date_refs) >= 1:
        score += 3.0
        result.details.append(f"Found {len(date_refs)} date/time references")
    else:
        result.penalties.append("No date references -- reader cannot assess recency")

    # Check for explicit YYYY-MM-DD dates and see if they are recent
    iso_dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
    recent_count = 0
    stale_count = 0
    for ds in iso_dates:
        try:
            d = datetime.strptime(ds, "%Y-%m-%d")
            if (today - d).days <= 7:
                recent_count += 1
            elif (today - d).days > 30:
                stale_count += 1
        except ValueError:
            pass

    if recent_count >= 2:
        score += 4.0
        result.details.append(f"{recent_count} dates within the last 7 days")
    elif recent_count >= 1:
        score += 2.0
        result.details.append(f"{recent_count} date within last 7 days")

    if stale_count >= 2:
        score -= 2.0
        result.penalties.append(f"{stale_count} dates are older than 30 days -- stale?")

    # Trending/new language
    freshness_words = re.findall(
        r"(?:新[增上收]|首次|刚刚|trending|new|fresh|just (?:launched|released)|"
        r"this week|本周|今[日天]|最新|首发|hot|rising|momentum|velocity|star.?gain)",
        text, re.IGNORECASE,
    )
    if len(freshness_words) >= 5:
        score += 6.0
        result.details.append(f"Strong freshness language ({len(freshness_words)} signals)")
    elif len(freshness_words) >= 2:
        score += 4.0
        result.details.append(f"Some freshness language ({len(freshness_words)} signals)")
    elif len(freshness_words) >= 1:
        score += 2.0
        result.details.append(f"Minimal freshness language")
    else:
        result.penalties.append("No freshness/trending language -- feels like a static list")

    # Star gain / velocity mentions (key freshness signal for our reports)
    velocity_refs = re.findall(
        r"(?:star.?gain|增[长速]|velocity|\+\d+\s*(?:stars?|⭐)|"
        r"(?:涨|新增|增加)\s*\d+\s*(?:star|⭐|颗星))",
        text, re.IGNORECASE,
    )
    if velocity_refs:
        score += 4.0
        result.details.append(f"Star velocity/gain mentioned ({len(velocity_refs)} refs)")
    else:
        result.penalties.append("No star gain/velocity data -- key for trending reports")

    result.score = min(max(score, 0.0), 20.0)
    return result


def score_completeness(text: str) -> DimensionResult:
    """Does the report have all required sections?"""
    result = DimensionResult(name="Completeness")

    # Detect report type
    is_weekly = bool(re.search(r"(?:周报|Weekly|Newsletter|New This Week)", text, re.IGNORECASE))
    sections = WEEKLY_REPORT_SECTIONS if is_weekly else DAILY_REPORT_SECTIONS
    report_type = "weekly" if is_weekly else "daily"
    result.details.append(f"Detected report type: {report_type}")

    # Check each required section
    found = 0
    total = len(sections)
    for section_id, pattern, label in sections:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            found += 1
            result.details.append(f"[OK] {label}")
        else:
            result.penalties.append(f"[MISSING] {label}")

    # Score proportionally
    section_score = (found / total) * 14.0  # up to 14 points for sections

    # Word/char count check
    char_count = len(text)
    word_count = len(text.split())

    if char_count >= 500:
        section_score += 3.0
        result.details.append(f"Content length: {char_count} chars / {word_count} words (adequate)")
    elif char_count >= 200:
        section_score += 1.5
        result.details.append(f"Content length: {char_count} chars (short)")
    else:
        result.penalties.append(f"Content too short: {char_count} chars (minimum ~500 for a report)")

    # Check for at least N tool entries (daily=10, weekly=15)
    tool_entries = re.findall(r"(?:^|\n)\s*\d+[\.\)、]", text)
    expected = 15 if is_weekly else 10
    if len(tool_entries) >= expected:
        section_score += 3.0
        result.details.append(f"Found {len(tool_entries)} numbered entries (expected {expected}+)")
    elif len(tool_entries) >= expected // 2:
        section_score += 1.5
        result.details.append(f"Found {len(tool_entries)} entries (expected {expected}+, partial)")
    else:
        result.penalties.append(f"Only {len(tool_entries)} numbered entries (expected {expected}+)")

    result.score = min(section_score, 20.0)
    return result


# ============================================================
# Main gate logic
# ============================================================

@dataclass
class GateResult:
    total_score: float
    verdict: str  # PASS, REVIEW, FAIL
    dimensions: list[DimensionResult] = field(default_factory=list)
    file_path: Optional[str] = None


def run_quality_gate(text: str, file_path: Optional[str] = None) -> GateResult:
    """Run all 5 scoring dimensions and return the gate result."""
    dimensions = [
        score_specificity(text),
        score_ai_detection(text),
        score_engagement(text),
        score_freshness(text),
        score_completeness(text),
    ]

    total = sum(d.score for d in dimensions)

    if total >= 80:
        verdict = "PASS"
    elif total >= 60:
        verdict = "REVIEW"
    else:
        verdict = "FAIL"

    return GateResult(
        total_score=round(total, 1),
        verdict=verdict,
        dimensions=dimensions,
        file_path=file_path,
    )


def format_report(gate: GateResult, verbose: bool = False) -> str:
    """Format the gate result as a human-readable report."""
    lines = []

    # Header
    verdict_icon = {"PASS": "PASS", "REVIEW": "REVIEW", "FAIL": "FAIL"}[gate.verdict]
    lines.append("=" * 60)
    lines.append(f"CONTENT QUALITY GATE -- {verdict_icon} ({gate.total_score}/100)")
    lines.append("=" * 60)

    if gate.file_path:
        lines.append(f"File: {gate.file_path}")

    lines.append("")

    # Dimension scores
    lines.append("DIMENSION SCORES:")
    lines.append("-" * 40)
    for dim in gate.dimensions:
        bar_filled = int(dim.score / dim.max_score * 10)
        bar = "#" * bar_filled + "." * (10 - bar_filled)
        lines.append(f"  {dim.name:<16} [{bar}] {dim.score:.0f}/{dim.max_score:.0f}")

    lines.append("-" * 40)
    lines.append(f"  {'TOTAL':<16}              {gate.total_score:.0f}/100")
    lines.append("")

    # Detailed feedback
    lines.append("DETAILED FEEDBACK:")
    lines.append("-" * 40)

    for dim in gate.dimensions:
        lines.append(f"\n  {dim.name} ({dim.score:.0f}/{dim.max_score:.0f}):")

        if dim.details:
            for detail in dim.details:
                lines.append(f"    + {detail}")

        if dim.penalties:
            for penalty in dim.penalties:
                lines.append(f"    - {penalty}")

    lines.append("")

    # Verdict and recommendations
    lines.append("=" * 60)
    if gate.verdict == "PASS":
        lines.append("VERDICT: PASS -- Content is ready to publish.")
    elif gate.verdict == "REVIEW":
        lines.append("VERDICT: REVIEW -- Content needs minor improvements.")
        weak = sorted(gate.dimensions, key=lambda d: d.score)
        lines.append(f"Priority fix: {weak[0].name} ({weak[0].score:.0f}/{weak[0].max_score:.0f})")
        if weak[0].penalties:
            lines.append(f"  Suggestion: {weak[0].penalties[0]}")
    else:
        lines.append("VERDICT: FAIL -- Content needs significant rework.")
        weak = sorted(gate.dimensions, key=lambda d: d.score)[:2]
        lines.append("Fix these first:")
        for w in weak:
            lines.append(f"  - {w.name} ({w.score:.0f}/{w.max_score:.0f})")
            if w.penalties:
                lines.append(f"    {w.penalties[0]}")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_json(gate: GateResult) -> str:
    """Format the gate result as JSON."""
    return json.dumps(
        {
            "file": gate.file_path,
            "total_score": gate.total_score,
            "verdict": gate.verdict,
            "dimensions": [
                {
                    "name": d.name,
                    "score": round(d.score, 1),
                    "max_score": d.max_score,
                    "details": d.details,
                    "penalties": d.penalties,
                }
                for d in gate.dimensions
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Content Quality Gate for Agent Skills Hub reports"
    )
    parser.add_argument("file", help="Path to the markdown report file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all details")
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if verdict is FAIL",
    )
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    text = file_path.read_text(encoding="utf-8")
    if not text.strip():
        print(f"Error: file is empty: {file_path}", file=sys.stderr)
        sys.exit(1)

    gate = run_quality_gate(text, file_path=str(file_path))

    if args.json:
        print(format_json(gate))
    else:
        print(format_report(gate, verbose=args.verbose))

    if args.exit_code and gate.verdict == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
