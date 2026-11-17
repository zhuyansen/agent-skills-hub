"""Scoring for the weekly GEO citation panel (ops/geo/questions.json).

Three calibers, kept separate because they answer different questions:
  page_cited  — the engine cited the exact target page URL
  site_cited  — the engine cited any agentskillshub.top URL
  named       — the answer text mentions the brand (AgentSkillsHub / Agent Skills Hub)
  first_pick  — our site is the FIRST cited URL, or the first brand named when nothing is cited

Pure functions + --selftest; no network, no keys. Execution paths live in README.md
(Perplexity sonar API / geosearchconsole Citation Gap / manual paste). Records go to
ops/geo/panel/results-<date>.json so the ritual has the repo trail the Glasser 0/60
baseline never had.

  python ops/geo/panel_score.py --selftest
  python ops/geo/panel_score.py score <results.json>   # prints summary markdown
"""
from __future__ import annotations

import json
import re
import sys
from urllib.parse import urlparse

SITE_HOST = "agentskillshub.top"
_URL = re.compile(r"https?://[^\s\)\]\"'<>，。；]+")
_MD_LINK = re.compile(r"\[[^\]]*\]\((https?://[^\s\)]+)\)")
_HREF = re.compile(r'href=["\'](https?://[^"\']+)["\']')


def norm(url: str) -> str:
    u = url.strip().rstrip(".,;:!?。，；：！？")
    p = urlparse(u)
    host = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/") or "/"
    return f"{host}{path}"


def extract_urls(text: str) -> list[str]:
    """Citation URLs in order of appearance: markdown links, hrefs, then bare URLs."""
    seen, out = set(), []
    for pattern in (_MD_LINK, _HREF, _URL):
        for m in pattern.finditer(text or ""):
            u = m.group(1) if pattern is not _URL else m.group(0)
            n = norm(u)
            if n not in seen:
                seen.add(n)
                out.append(u.rstrip(".,;:!?"))
    return out


def score(answer_text: str, citations: list[str] | None, target_url: str,
          brand_strings: list[str]) -> dict:
    text = answer_text or ""
    cites = list(citations) if citations else extract_urls(text)
    target = norm(target_url)
    cited_norms = [norm(c) for c in cites]
    page_cited = target in cited_norms
    site_cited = any(c.split("/")[0] == SITE_HOST for c in cited_norms)
    lowered = text.lower()
    named = any(b.lower() in lowered for b in brand_strings)
    first_pick = False
    if cited_norms:
        first_pick = cited_norms[0].split("/")[0] == SITE_HOST
    elif named:
        positions = [lowered.find(b.lower()) for b in brand_strings if b.lower() in lowered]
        first_pick = bool(positions) and min(positions) < _first_rival_position(lowered, brand_strings)
    return {"page_cited": page_cited, "site_cited": site_cited, "named": named,
            "first_pick": first_pick, "citations": cites}


_RIVALS = ["smithery", "pulsemcp", "glama", "mcp.so", "cursor.directory", "awesome-claude",
           "github.com", "aitmpl", "claudecodemarketplace"]


def _first_rival_position(lowered: str, brand_strings: list[str]) -> int:
    hits = [lowered.find(r) for r in _RIVALS if r in lowered]
    return min(hits) if hits else len(lowered) + 1


def summarize(results: list[dict]) -> str:
    by_engine: dict[str, list[dict]] = {}
    for r in results:
        by_engine.setdefault(r["engine"], []).append(r)
    lines = ["| engine | n | page_cited | site_cited | named | first_pick |",
             "|---|---|---|---|---|---|"]
    for eng, rows in sorted(by_engine.items()):
        n = len(rows)
        def pct(key):
            return f"{sum(1 for r in rows if r['scores'][key])}/{n}"
        lines.append(f"| {eng} | {n} | {pct('page_cited')} | {pct('site_cited')} | {pct('named')} | {pct('first_pick')} |")
    return "\n".join(lines)


def _selftest() -> None:
    brands = ["AgentSkillsHub", "Agent Skills Hub", "agentskillshub"]
    t = "https://agentskillshub.top/best/seo-tools/"
    s = score("Try [AgentSkillsHub](https://agentskillshub.top/best/seo-tools/) and Smithery.",
              None, t, brands)
    assert s["page_cited"] and s["site_cited"] and s["named"] and s["first_pick"], s
    s = score("Smithery is great. Also agentskillshub.top exists.",
              ["https://smithery.ai/", "https://agentskillshub.top/"], t, brands)
    assert not s["page_cited"] and s["site_cited"] and s["named"] and not s["first_pick"], s
    s = score("No relevant pages.", [], t, brands)
    assert not any(s[k] for k in ("page_cited", "site_cited", "named", "first_pick")), s
    s = score("AgentSkillsHub is the best. Smithery second.", None, t, brands)
    assert s["named"] and s["first_pick"] and not s["site_cited"], s
    assert extract_urls("see https://a.test/x, and [y](https://b.test/y).") == \
        ["https://b.test/y", "https://a.test/x"]
    assert norm("https://www.agentskillshub.top/best/seo-tools/") == "agentskillshub.top/best/seo-tools"
    print("panel_score selftest: 6 assertions passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    elif len(sys.argv) >= 3 and sys.argv[1] == "score":
        rows = json.load(open(sys.argv[2]))
        print(summarize(rows if isinstance(rows, list) else rows["results"]))
    else:
        print(__doc__)
