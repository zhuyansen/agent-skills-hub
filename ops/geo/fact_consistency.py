#!/usr/bin/env python3
"""Fact consistency across the AgentSkillsHub entity graph (node 7 of entity_audit.py).

The other nodes check that links between the graph's nodes exist. This one checks
that the nodes say the same thing: directory size, launch date, rule count, founder,
and that look-alike domains only appear in a disclaimer. A model that reads 280,000+
on the site and 130K+ in the MCP server card has two facts to pick from, and may
pick the stale one.

A page is read as its visible text, its three summary tags (description, og:description,
twitter:description) and its JSON-LD. Until 2026-11-27 the summary tags were dropped, so
/ai-info/ called the index total "graded" in all three and nothing noticed. A count whose
own clause says graded is judged against the graded count, one that says indexed against
the index total; a count whose clause says neither, or both, may match either.

Facts live in brand-facts.json:
  - live facts must agree everywhere (the directory size is read from the homepage,
    so it follows the real count instead of being typed in);
  - snapshot facts (dataset DOIs, dated reports) may differ from the live count,
    but only next to their DOI or report name.

Usage:
  python3 ops/geo/fact_consistency.py          # fetch the nodes and print the report
  python3 ops/geo/fact_consistency.py --json
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

GEO_DIR = Path(__file__).resolve().parent
LEDGER_PATH = GEO_DIR / "brand-facts.json"
SITE = "https://agentskillshub.top"

# name -> (url, kind). kind picks how the response body becomes text.
SOURCES: dict[str, tuple[str, str]] = {
    "site_home": (f"{SITE}/", "html"),
    "site_about": (f"{SITE}/about/", "html"),
    "site_ai_info": (f"{SITE}/ai-info/", "html"),
    "site_contact": (f"{SITE}/contact/", "html"),
    "site_how_we_grade": (f"{SITE}/how-we-grade/", "html"),
    "site_llms_txt": (f"{SITE}/llms.txt", "text"),
    "site_mcp_server_card": (f"{SITE}/.well-known/mcp/server-card.json", "text"),
    "github_repo": ("https://api.github.com/repos/zhuyansen/agent-skills-hub", "github_repo"),
    "github_readme": ("https://raw.githubusercontent.com/zhuyansen/agent-skills-hub/main/README.md", "text"),
    "npm_cli": ("https://registry.npmjs.org/%40agentskillshub%2Fcli", "npm"),
    "npm_mcp": ("https://registry.npmjs.org/%40agentskillshub%2Fmcp", "npm"),
    "wikidata_org": ("https://www.wikidata.org/wiki/Special:EntityData/Q141986406.json", "wikidata"),
    "wikidata_dataset": ("https://www.wikidata.org/wiki/Special:EntityData/Q141735092.json", "wikidata"),
    "zenodo_21292799": ("https://zenodo.org/api/records/21292799", "zenodo"),
    # The concept record answers with its newest version; 24387074 was version 1, superseded on 2026-11-21.
    "zenodo_24387073": ("https://zenodo.org/api/records/24387073", "zenodo"),
    # The other two sites state the product's facts too: on 2026-11-27 the company's home page still said
    # 42 rules (the ledger says 44) and no check read it.
    "company_home": ("https://gosailglobal.com/", "html"),
    "jasonzhu_about": ("https://jasonzhu.ai/en/about", "html"),
    "jasonzhu_llms_txt": ("https://jasonzhu.ai/llms.txt", "text"),
}

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
COUNT_RE = re.compile(
    r"(?<![\w.,])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?\s?[KkMm]\b|\d{5,})\+?\s*"
    r"(?:[A-Za-z-]+\s){0,3}?"
    r"(?:skills|Skills|repositories|repos|projects|tools|Tools|MCP servers)\b"
)
DATE_RE = re.compile(
    r"(?:launch(?:ed)?|found(?:ed|ing)|inception|上线|成立)[^.。\n]{0,40}?"
    rf"(20\d\d-\d\d-\d\d|20\d\d-\d\d(?!-)|(?:{MONTHS}) \d{{1,2}}, 20\d\d)",
    re.I,
)
RULES_RE = re.compile(r"(?<![\w.])(\d{1,3})[- ](?:(?:published|static|security|grading|scanning)[- ]){0,2}rules?\b", re.I)
FOUNDER_RE = re.compile(r"(?:founded by|founder)[:,]?\s+(?:and maintainer\s+)?([A-Z][a-z]+(?: [A-Z][a-z]+)?)")
DISCLAIMER_RE = re.compile(r"not affiliated|unaffiliated|\bnor\b|no affiliation|无关|无任何关联|没有关联|不隶属|非本平台|not the same", re.I)

# Which live count a number names, read from its own clause (2026-11-27).
GRADED_WORDS = re.compile(r"grad(?:ed|es|ing)\b|评级", re.I)
INDEXED_WORDS = re.compile(r"\bindex(?:ed|es|ing)?\b|收录", re.I)
# "·", "|" and dashes separate items in a tagline ("267,000+ projects · security-graded + quality-scored").
CLAUSE_END = re.compile(r"[.;:!?。；：！？,，()（）\n·•|—–]")
COUNT_LABEL = {"directory_size": "indexed", "graded_count": "graded"}
SUMMARY_TAGS = ("description", "og:description", "twitter:description")
META_TAG = re.compile(r"<meta\b[^>]*>", re.I)
META_ATTR = re.compile(r'([\w:-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')')


# ---------------------------------------------------------------- text extraction

def meta_summaries(body: str) -> list[str]:
    """A page's description, og:description and twitter:description, each text once."""
    out: dict[str, None] = {}
    for tag in META_TAG.findall(body):
        attrs = {m.group(1).lower(): m.group(2) if m.group(2) is not None else m.group(3) for m in META_ATTR.finditer(tag)}
        if (attrs.get("name") or attrs.get("property") or "").lower() in SUMMARY_TAGS and attrs.get("content"):
            out[attrs["content"]] = None
    return list(out)


def html_to_text(body: str) -> str:
    """Visible text, the summary tags and JSON-LD (structured claims count as claims)."""
    ld = " ".join(re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', body, re.I | re.S))
    summaries = " . ".join(meta_summaries(body))
    body = re.sub(r"<(script|style|noscript)\b.*?</\1>", " ", body, flags=re.I | re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", html_lib.unescape(body + " . " + summaries + " . " + ld)).strip()


def body_to_text(kind: str, body: str) -> str:
    if kind == "html":
        return html_to_text(body)
    if kind == "text":
        return re.sub(r"\s+", " ", body)
    data = json.loads(body)
    if kind == "github_repo":
        parts = [data.get("description") or "", data.get("homepage") or ""]
    elif kind == "npm":
        parts = [data.get("description") or "", data.get("readme") or ""]
    elif kind == "zenodo":
        md = data.get("metadata", {})
        parts = [md.get("title", ""), html_to_text(md.get("description", ""))]
    elif kind == "wikidata":
        ent = next(iter(data.get("entities", {}).values()), {})
        parts = [v.get("value", "") for v in ent.get("labels", {}).values()]
        parts += [v.get("value", "") for v in ent.get("descriptions", {}).values()]
        for claim in ent.get("claims", {}).get("P571", []):  # inception, with its precision
            t = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
            if t.get("time"):
                ymd = t["time"].lstrip("+")[:10]
                precision = t.get("precision", 11)
                parts.append("inception " + (ymd[:4] if precision <= 9 else ymd[:7] if precision == 10 else ymd))
    else:
        raise ValueError(f"unknown kind {kind}")
    return re.sub(r"\s+", " ", " ".join(parts))


# ---------------------------------------------------------------- parsing helpers

def parse_count(raw: str) -> int:
    s = raw.replace(",", "").replace(" ", "")
    mult = 1
    if s[-1] in "Kk":
        mult, s = 1_000, s[:-1]
    elif s[-1] in "Mm":
        mult, s = 1_000_000, s[:-1]
    return int(round(float(s) * mult))


def normalize_date(raw: str) -> str:
    m = re.match(rf"({MONTHS}) (\d{{1,2}}), (20\d\d)", raw, re.I)
    if m:
        month = MONTHS.split("|").index(m.group(1).capitalize()) + 1
        return f"{m.group(3)}-{month:02d}-{int(m.group(2)):02d}"
    return raw


def window(text: str, start: int, end: int, size: int = 300) -> str:
    return text[max(0, start - size): end + size]


def snippet(text: str, start: int, end: int, size: int = 70) -> str:
    return "…" + text[max(0, start - size): end + size].strip() + "…"


def count_field(text: str, start: int, end: int) -> str | None:
    """'graded_count' or 'directory_size' when the number's own clause says which, else None.

    "287,000+ skills & MCP servers graded on 44 rules" names the graded count; "Indexed Repositories
    287,000+" the index; "287,000+ skills, every popular one security-graded" neither: the comma ends
    the number's clause before "graded".
    """
    before = text[max(0, start - 40):start]
    cuts = list(CLAUSE_END.finditer(before))
    if cuts:
        before = before[cuts[-1].end():]
    after = text[end:end + 40]
    cut = CLAUSE_END.search(after)
    if cut:
        after = after[:cut.start()]
    clause = before + text[start:end] + after
    graded, indexed = bool(GRADED_WORDS.search(clause)), bool(INDEXED_WORDS.search(clause))
    return "graded_count" if graded and not indexed else "directory_size" if indexed and not graded else None


# ---------------------------------------------------------------- the check

LIVE_COUNTS = ("directory_size", "graded_count")


def live_count(texts: dict[str, tuple[str, str]], ledger: dict[str, Any], fact: str) -> int | None:
    """Read a live count from its canonical page, so the ledger never holds a stale number."""
    spec = ledger["live"].get(fact)
    src = texts.get(spec["canonical_source"]) if spec else None
    if not src:
        return None
    m = re.search(spec["canonical_pattern"], src[1])
    return parse_count(m.group(1)) if m else None


def check_texts(texts: dict[str, tuple[str, str]], ledger: dict[str, Any]) -> dict[str, Any]:
    """texts: source name -> (url, plain text). Pure function: no network."""
    live = ledger["live"]
    size_spec = live["directory_size"]
    live_values = {f: live_count(texts, ledger, f) for f in LIVE_COUNTS if f in live}
    live_size = live_values.get("directory_size")
    # A count is judged against both live counts; with either unread (its page did not load),
    # every correct number for it would read as stale. Skip the counts, say so, check the rest.
    unread = [f for f, v in live_values.items() if not v]
    expected_counts = " or ".join(f"~{v:,}+ ({f})" for f, v in live_values.items() if v) or "live counts unreadable"
    conflicts: list[dict[str, Any]] = []
    snapshot_hits: list[dict[str, Any]] = []
    per_source: dict[str, dict[str, Any]] = {}

    def add(fact: str, name: str, url: str, found: Any, expected: Any, text: str, s: int, e: int, why: str) -> None:
        conflicts.append({
            "fact": fact, "source": name, "url": url, "found": found,
            "expected": expected, "why": why, "snippet": snippet(text, s, e),
        })

    for name, (url, text) in texts.items():
        is_snapshot_source = name in ledger.get("snapshot_sources", [])
        counts_seen: list[int] = []

        # 1. directory size
        for m in ([] if unread else COUNT_RE.finditer(text)):
            value = parse_count(m.group(1))
            if value < size_spec["min_count"]:
                continue
            counts_seen.append(value)
            ctx = window(text, m.start(), m.end())
            if any(oc["count"] == value and oc["context"] in ctx for oc in ledger.get("other_counts", [])):
                continue
            field = count_field(text, m.start(), m.end())
            matches = {f for f, v in live_values.items() if v and abs(value - v) <= live[f]["tolerance"] * v}
            if matches and (field is None or field in matches):
                continue
            # A snapshot next to its DOI is judged as the snapshot, even when it also lands near a live count.
            snap = next((sp for sp in ledger["snapshots"] if abs(value - sp["count"]) <= 0.01 * sp["count"]), None)
            if snap and (is_snapshot_source or any(a in ctx for a in snap["anchors"])):
                snapshot_hits.append({"source": name, "snapshot": snap["name"], "found": m.group(0).strip()})
                continue
            if field and matches:
                other = next(iter(matches))
                add("skill_count", name, url, m.group(0).strip(), f"~{live_values[field]:,}+ ({field})", text,
                    m.start(), m.end(), f"the sentence calls it {COUNT_LABEL[field]}, but it is the "
                                        f"{COUNT_LABEL[other]} count (~{live_values[other]:,}+)")
                continue
            if is_snapshot_source:
                continue  # a dataset record describing its own contents
            why = (f"equals snapshot '{snap['name']}' but nothing near it says so; reads as the live count"
                   if snap else "matches neither the live count nor any snapshot")
            add("skill_count", name, url, m.group(0).strip(), expected_counts, text, m.start(), m.end(), why)

        # 2. launch date (lower precision is fine if it agrees: 2026-03 vs 2026-03-08)
        own_dates = name in live["launch_date"].get("not_in_sources", [])
        for m in ([] if own_dates else DATE_RE.finditer(text)):
            found = normalize_date(m.group(1))
            if not live["launch_date"]["value"].startswith(found):
                add("launch_date", name, url, found, live["launch_date"]["value"], text, m.start(), m.end(),
                    "launch/founding date differs from the ledger")

        # 3. rule count
        for m in RULES_RE.finditer(text):
            n = int(m.group(1))
            if n != live["security_rules"]["value"]:
                add("security_rules", name, url, n, live["security_rules"]["value"], text, m.start(), m.end(),
                    "rule count differs from the ledger")

        # 4. founder
        for m in FOUNDER_RE.finditer(text):
            who = m.group(1)
            if not any(who.lower() in f.lower() or f.lower() in who.lower() for f in live["founder_names"]):
                add("founder", name, url, who, live["founder_names"][0], text, m.start(), m.end(),
                    "a founder name not in the ledger")

        # 5. look-alike domains only inside a disclaimer
        for dom in ledger.get("foreign_domains", []):
            for m in re.finditer(re.escape(dom), text):
                if not DISCLAIMER_RE.search(window(text, m.start(), m.end(), 200)):
                    add("foreign_domain", name, url, dom, "only in a 'not affiliated' sentence", text, m.start(), m.end(),
                        "look-alike domain mentioned without a disclaimer nearby")

        per_source[name] = {"url": url, "chars": len(text), "counts_seen": sorted(set(counts_seen))}

    return {
        "live_directory_size": live_size,
        "live_graded_count": live_values.get("graded_count"),
        "counts_skipped": (f"live count unread: {', '.join(unread)}" if unread else ""),
        "conflicts": conflicts,
        "snapshot_mentions_ok": snapshot_hits,
        "sources": per_source,
    }


def audit_fact_consistency(http_get: Callable[..., tuple[int, dict[str, str], str]],
                           ledger_path: Path = LEDGER_PATH) -> dict[str, Any]:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    texts: dict[str, tuple[str, str]] = {}
    fetch_errors: dict[str, str] = {}
    for name, (url, kind) in SOURCES.items():
        code, _, body = http_get(url)
        if code != 200:
            fetch_errors[name] = f"HTTP {code}"
            continue
        try:
            texts[name] = (url, body_to_text(kind, body))
        except Exception as exc:  # malformed JSON from a registry, say
            fetch_errors[name] = f"parse error: {exc}"
    result = check_texts(texts, ledger)
    if result["conflicts"]:
        status = "CONFLICTS_FOUND"
    elif fetch_errors or result["counts_skipped"]:
        status = "PARTIAL_FETCH"
    else:
        status = "VERIFIED"
    by_fact: dict[str, int] = {}
    for c in result["conflicts"]:
        by_fact[c["fact"]] = by_fact.get(c["fact"], 0) + 1
    return {
        "node": "7_Fact_Consistency",
        "status": status,
        "sources_checked": len(texts),
        "fetch_errors": fetch_errors,
        "conflicts_by_fact": by_fact,
        **result,
    }


def print_report(node: dict[str, Any]) -> None:
    print(f"=== Fact consistency: {node['status']} ===")
    fmt = lambda v: f"{v:,}+" if v else "unreadable"  # noqa: E731
    print(f"Live counts: indexed {fmt(node['live_directory_size'])} (homepage), graded {fmt(node['live_graded_count'])} (/ai-info/)"
          f" | sources read: {node['sources_checked']}")
    for name, err in node["fetch_errors"].items():
        print(f"  ! {name}: {err}")
    if not node["conflicts"]:
        print("No conflicts.")
    for c in node["conflicts"]:
        print(f"\n  [{c['fact']}] {c['source']}  found: {c['found']}  expected: {c['expected']}")
        print(f"    {c['why']}")
        print(f"    {c['url']}")
        print(f"    {c['snippet']}")
    print(f"\nSnapshot mentions with their DOI/report nearby: {len(node['snapshot_mentions_ok'])}")


def main() -> int:
    sys.path.insert(0, str(GEO_DIR))
    from entity_audit import http_get  # same UA and timeouts as the rest of the audit

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    node = audit_fact_consistency(http_get)
    from fact_todos import build_todos, github_has_via
    node["todos"] = build_todos(node, GEO_DIR.parents[1], github_has_via(http_get))
    if args.json:
        print(json.dumps(node, ensure_ascii=False, indent=2))
    else:
        print_report(node)
    return 0


if __name__ == "__main__":
    sys.exit(main())
