#!/usr/bin/env python3
"""Paper arXiv:2604.25707 Evidence-Container + Brand Self-Attribution Auditor.

Checks target URLs on agentskillshub.top against the 6 operational criteria
derived from Section 9.1 of `From Citation Selection to Citation Absorption`
combined with Suski First-50-Words brand attribution:
  1. Definition block       (clear 'What is ...' / definitional sentence)
  2. Quantitative evidence  (>=5 concrete numbers/metrics in main text)
  3. Comparison block       (HTML <table> comparing >=2 options)
  4. Procedural steps       (<ol> or explicit numbered step sequence)
  5. Top-90-word brand lock (`Agent Skills Hub` AND `agentskillshub.top` near top)
  6. Modularity & Q&A guard (>=1,000 words, >=5 H2s, not a thin FAQ wrapper)

Usage:
  python3 ops/geo/evidence_container_audit.py
  python3 ops/geo/evidence_container_audit.py https://agentskillshub.top/best/code-review/
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from typing import Any

UA = "AgentSkillsHub-EvidenceAudit/1.0 (+https://agentskillshub.top/ai-info/)"

DEFAULT_URLS = [
    "https://agentskillshub.top/how-we-grade/",
    "https://agentskillshub.top/best/code-review/",
    "https://agentskillshub.top/best/cli-tools/",
    "https://agentskillshub.top/best/secret-detection/",
    "https://agentskillshub.top/best/skill-management-tools/",
    "https://agentskillshub.top/best/content-syndication/",
    "https://agentskillshub.top/best/knowledge-base/",
    "https://agentskillshub.top/best/3d-mcp/",
]


def audit_url(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "ignore")

    h2s = [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.S | re.I)]
    tables = len(re.findall(r"<table\b", html, re.I))
    ols = len(re.findall(r"<ol\b", html, re.I))
    uls = len(re.findall(r"<ul\b", html, re.I))

    body_text = re.sub(r"<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<footer.*?</footer>|<[^>]+>", " ", html, flags=re.S | re.I)
    body_text = re.sub(r"\s+", " ", body_text).strip()
    words = body_text.split()
    word_count = len(words)
    first_120 = " ".join(words[:120])

    # 1. Definition
    has_definition = bool(
        re.search(r"what is\b|definition|defined as|\bis an? (open-source|tool|skill|framework|directory|methodology)", body_text[:3500], re.I)
    )
    # 2. Quantitative evidence
    num_hits = re.findall(r"\b\d[\d,\.]*(?:%|\+|k|x|×|★|/100|/8|/12)?\b", body_text[:4000], re.I)
    has_numbers = len(num_hits) >= 8
    # 3. Comparison table
    has_comparison = tables >= 1
    # 4. Procedural steps
    has_steps = ols >= 1 or bool(re.search(r"step\s*1\b|how to (use|install|choose|verify|audit)", body_text, re.I))
    # 5. Brand + domain self-attribution near top
    has_brand_name_top = "agent skills hub" in first_120.lower()
    has_domain_top = "agentskillshub.top" in first_120.lower()
    has_doi = "10.5281/zenodo" in html
    # 6. Modularity (non-thin Q&A)
    q_h2_ratio = sum(1 for h in h2s if "?" in h) / max(1, len(h2s))
    good_structure = word_count >= 1000 and len(h2s) >= 5 and q_h2_ratio < 0.6

    checks = {
        "1_definition": has_definition,
        "2_numbers": has_numbers,
        "3_comparison_table": has_comparison,
        "4_procedural_steps": has_steps,
        "5_brand_and_domain_top120": has_brand_name_top and has_domain_top,
        "6_modular_structure": good_structure,
    }
    score = sum(1 for ok in checks.values() if ok)
    missing = [k for k, ok in checks.items() if not ok]
    return {
        "url": url,
        "score": f"{score}/6",
        "words": word_count,
        "h2s": len(h2s),
        "tables": tables,
        "ols": ols,
        "brand_top": has_brand_name_top,
        "domain_top": has_domain_top,
        "has_doi": has_doi,
        "missing": missing,
    }


def main() -> int:
    urls = sys.argv[1:] or DEFAULT_URLS
    results = []
    print(f"{'Score':<6} {'Words':>6} {'Tbl':>3} {'OL':>2} {'DomTop':>6}  {'URL':<56} Missing")
    print("-" * 115)
    for u in urls:
        try:
            r = audit_url(u)
            results.append(r)
            short = u.replace("https://agentskillshub.top", "")
            print(
                f"{r['score']:<6} {r['words']:>6} {r['tables']:>3} {r['ols']:>2} "
                f"{('YES' if r['domain_top'] else 'NO'):>6}  {short:<56} {', '.join(r['missing']) or 'ALL PASS'}"
            )
        except Exception as e:
            print(f"ERR    {u}: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
