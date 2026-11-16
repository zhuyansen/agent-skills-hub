"""On-page check for the scenario pages (/best/<slug>/), run after a deploy.

  python ops/seo/page_check.py <report.md> --changed <base-sha> <head-sha>
  python ops/seo/page_check.py <report.md> --all
  python ops/seo/page_check.py <report.md> --slugs ppt-presentation,claude-video-skills

Our own version of the checks 哥飞's On Page audit (seo.web.cafe/audit/) took points off
for on 2026-10-05: title over 60 characters, ~9K words per page, card text ("view details",
"python mit") outranking the page's own keyword in the word-frequency list. It reads the
live HTML, so it sees what Google sees. Free; the report links each page to 哥飞's audit
for the full score (1 credit from the daily web allowance, when the owner clicks).

Target keyword per page: `seo_keyword` in scenario-keywords.json if set; else the page's
GSC query of two to four words with the most impressions over the last 28 days that
shares two thirds of its content words with the page's subject (best/top/tool/skill/ai/claude
and numbers don't count) (the top query alone can be an
odd long tail, "china web scraper software market", a repo name, "jev ultrafast", or an
operator search, "%site.developers.openai.com codex skills"); else the subject itself:
`serp_subject` if set, or the title before the colon. The report says which one it used.
Words are compared without a plural s ("claude video skill" = "claude video skills").

Length: a long page only gets a warning. 哥飞's own ruling (Agent, 10-05): on an aggregate
page length is not the problem, the core word must lead the word-frequency list; that is
the check that fails.
--changed checks the pages whose scenario entries changed between two commits, or all
live pages when the generator or a shared file changed; nothing changed = no report.
"""
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = "frontend/scripts"
KEYWORDS_FILE = f"{SCRIPTS}/scenario-keywords.json"
PER_SLUG_FILES = [f"{SCRIPTS}/scenario-desc-zh.json", f"{SCRIPTS}/scenario-kinds.json", f"{SCRIPTS}/scenario-zh.json"]
SHARED_FILES = [f"{SCRIPTS}/generate-scenario-pages.mjs", f"{SCRIPTS}/scenario-kinds.mjs", f"{SCRIPTS}/shared-utils.mjs"]
SITE = "https://agentskillshub.top"
# Where pages are read from; the checks still judge them as SITE pages (canonical etc.).
# Set to a local server over frontend/dist to compare a build before pushing it.
FETCH_BASE = os.environ.get("PAGE_CHECK_FETCH_BASE", SITE)
UA = "Mozilla/5.0 (compatible; agentskillshub-pagecheck/1.0; +https://agentskillshub.top)"
PASS_SCORE = 90
TITLE_MAX, TITLE_HARD = 60, 75
DESC_MIN, DESC_MAX = 70, 160
WORDS_MIN, WORDS_IDEAL = 600, 1800
QUERY_WORDS = (2, 4)   # GSC queries considered as a page's target
HTML_MAX_KB = 500
DENSITY_TOP = 3        # the keyword should be among the top n-grams of its own length
_WORD = re.compile(r"[a-z0-9]+(?:[.'][a-z0-9]+)*")
_PLAIN_QUERY = re.compile(r"^[a-z0-9 ]+$")
SUBJECT_SHARE = 0.67  # of a query's content words (GENERIC left out) must be in the subject
GENERIC = {"best", "top", "free", "tool", "skill", "ai", "for", "the", "and", "of", "in", "with", "to", "a", "list",
           "open", "source", "claude", "code"}
EDGE_GENERIC = GENERIC - {"claude", "code"}   # trimmed off a keyword's ends; "claude code hooks" stays whole
FUNCTION_WORDS = {"the", "a", "an", "and", "or", "of", "in", "on", "for", "to", "with", "by", "is", "it", "from", "at",
                  "as", "this", "that", "your", "you"}


# --- which pages ---------------------------------------------------------------------------

def _git_json(sha: str, path: str):
    try:
        return json.loads(subprocess.run(["git", "show", f"{sha}:{path}"], cwd=ROOT, capture_output=True,
                                         text=True, check=True).stdout)
    except (subprocess.CalledProcessError, ValueError):
        return None


def live_pages() -> dict[str, dict]:
    pages = json.loads((ROOT / KEYWORDS_FILE).read_text())
    return {p["slug"]: p for p in pages if not p.get("retired")}


def changed_slugs(base: str, head: str) -> list[str]:
    """Live pages whose own entries differ between two commits; all of them when a shared file did."""
    live = live_pages()
    diff = subprocess.run(["git", "diff", "--name-only", base, head], cwd=ROOT, capture_output=True, text=True).stdout
    if any(f in diff.split() for f in SHARED_FILES):
        return sorted(live)
    old = {p["slug"]: p for p in (_git_json(base, KEYWORDS_FILE) or [])}
    new = {p["slug"]: p for p in (_git_json(head, KEYWORDS_FILE) or [])}
    changed = {s for s in new if new[s] != old.get(s)}
    for path in PER_SLUG_FILES:
        a, b = _git_json(base, path) or {}, _git_json(head, path) or {}
        changed |= {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
    return sorted(s for s in changed if s in live)


# --- what the page should rank for ----------------------------------------------------------

def gsc_top_queries() -> dict[str, list[tuple[str, int]]]:
    """Page URL -> its query with the most impressions, last 28 days. Empty when GSC is not set up."""
    try:
        sys.path.insert(0, str(ROOT / "ops/gsc"))
        import fetch_gsc as g
        svc = g.get_service()
        end = date.today() - timedelta(days=3)
        rows = g.query(svc, g.pick_site(svc), end - timedelta(days=27), end, ["page", "query"], limit=25000)
    except Exception:  # noqa: BLE001 — no GSC credentials: fall back to the title
        return {}
    return pick_queries(rows)


def pick_queries(rows: list[dict]) -> dict[str, list[tuple[str, int]]]:
    """Per page, its plain 2-4-word queries by impressions, most first."""
    out: dict[str, list[tuple[str, int]]] = {}
    lo, hi = QUERY_WORDS
    for r in rows:
        q = r["query"].lower().strip()
        if _PLAIN_QUERY.match(q) and lo <= len(q.split()) <= hi:
            out.setdefault(r["page"], []).append((q, r["impressions"]))
    return {p: sorted(qs, key=lambda x: -x[1]) for p, qs in out.items()}


def stem(word: str) -> str:
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def stems(text: str) -> list[str]:
    return [stem(w) for w in _WORD.findall(text.lower())]


def subject(page: dict, title: str) -> str:
    """The title's subject. "A & B Nouns" keeps the head noun: "Claude & Codex Design
    Skills" is "claude design skills", not "claude" (ai-design's target until 10-06)."""
    raw = page.get("serp_subject") or title
    head = re.split(r"[:|]", raw)[0].split(",")[0].lower()
    if "&" in head:
        left, right = (part.split() for part in head.split("&", 1))
        head = " ".join(left + right[1:] if len(left) == 1 and len(right) > 1 else left)
    return " ".join(head.split())


def target_keyword(page: dict, title: str, gsc: dict[str, list[tuple[str, int]]]) -> tuple[str, str]:
    if page.get("seo_keyword"):
        return page["seo_keyword"].lower(), "配置"
    subj = subject(page, title)
    base = set(stems(subj))
    for q, _ in gsc.get(f"{SITE}/best/{page['slug']}/", []):
        words = [w for w in stems(q) if w not in GENERIC and not w.isdigit()]
        if words and sum(w in base for w in words) >= SUBJECT_SHARE * len(words):
            return q, "GSC"
    return subj, "标题"


# --- reading the page ----------------------------------------------------------------------

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as res:
        return res.read().decode("utf-8", "replace")


def _meta(s: str, pattern: str) -> str:
    m = re.search(pattern, s, re.I | re.S)
    return html.unescape(m.group(1)).strip() if m else ""


TABLE_CELLS_MIN = 30
BOLD_MIN = 5
H2_MIN, H2_MAX = 6, 12
_BLUF_RE = re.compile(
    r"\b(?:the\s+best\b[^.!?]{1,120}\b(?:is|are|depends\s+on)|our\s+(?:top\s+)?pick\b[^.!?]{0,80}\bis|top\s+pick\b)",
    re.I,
)
_URL_YEAR_RE = re.compile(r"/best/[^/]*\b20\d{2}\b[^/]*/")
_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
_YEAR_RE = re.compile(r"\b(20\d{2})\b")


def parse(s: str) -> dict:
    body = re.sub(r"<(script|style|noscript)\b.*?</\1>", " ", s, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    imgs = re.findall(r"<img\b[^>]*>", s, re.I)
    words = _WORD.findall(text.lower())
    ld_dates = re.findall(r'"(?:dateModified|lastReviewed)"\s*:\s*"(\d{4}-\d{2}-\d{2})"', s)
    vis_dates = re.findall(
        r"(?:Reviewed|Tested|Updated|Last\s+reviewed|Last\s+updated|实测|复核|更新)[^<\n]{0,40}?(\d{4}-\d{2}-\d{2})",
        s,
        re.I,
    )
    return {
        "title": _meta(s, r"<title[^>]*>(.*?)</title>"),
        "description": _meta(s, r'<meta[^>]+name="description"[^>]+content="([^"]*)"'),
        "canonical": _meta(s, r'<link[^>]+rel="canonical"[^>]+href="([^"]*)"'),
        "robots": _meta(s, r'<meta[^>]+name="robots"[^>]+content="([^"]*)"'),
        "h1": [html.unescape(re.sub(r"<[^>]+>", "", h)).strip() for h in re.findall(r"<h1\b[^>]*>(.*?)</h1>", s, re.S | re.I)],
        "h2": len(re.findall(r"<h2\b", body, re.I)),
        "table_cells": len(re.findall(r"<t[dh]\b", body, re.I)),
        "bold_spans": len(re.findall(r"<(?:strong|b)\b", body, re.I)),
        "first_100_text": " ".join(text.split()[:100]),
        "ld_dates": sorted(set(ld_dates)),
        "vis_dates": sorted(set(vis_dates)),
        "words": words,
        "kb": len(s.encode()) // 1024,
        "jsonld": len(re.findall(r'type="application/ld\+json"', s)),
        "imgs_bad": sum(1 for i in imgs if not re.search(r"\balt=", i) or not re.search(r"\bwidth=", i)),
    }


def ngram_rank(words: list[str], phrase: str) -> tuple[int | None, list[tuple[str, int]]]:
    """Rank of `phrase` among the page's n-grams of the same length, and the top five
    (both sides without plural s)."""
    words, phrase = [stem(w) for w in words], " ".join(stems(phrase))
    n = len(phrase.split())
    grams = (words[i:i + n] for i in range(len(words) - n + 1))
    counts = Counter(" ".join(g) for g in grams if not all(w in FUNCTION_WORDS for w in g))
    ranked = counts.most_common()
    rank = next((i + 1 for i, (g, _) in enumerate(ranked) if g == phrase), None)
    return rank, ranked[:5]


# --- the checks ----------------------------------------------------------------------------

def _has(text: str, kw: str) -> bool:
    return f" {' '.join(stems(kw))} " in f" {' '.join(stems(text))} "


def _meta_checks(p: dict, kw: str, url: str) -> list[tuple[str, str, str]]:
    t, d = len(p["title"]), len(p["description"])
    places = (p["title"], " ".join(p["h1"]), p["description"])
    return [
        ("标题长度", "ok" if t <= TITLE_MAX else "warn" if t <= TITLE_HARD else "fail", f"{t} 字符"),
        ("描述长度", "ok" if DESC_MIN <= d <= DESC_MAX else "warn", f"{d} 字符"),
        ("canonical", "ok" if p["canonical"] == url else "fail", p["canonical"] or "无"),
        ("可收录", "fail" if "noindex" in p["robots"].lower() else "ok", p["robots"] or "未设"),
        ("唯一 H1", "ok" if len(p["h1"]) == 1 else "fail", f"{len(p['h1'])} 个"),
        ("关键词在标题/H1/描述", "ok" if all(_has(x, kw) for x in places) else "warn",
         "/".join("✓" if _has(x, kw) else "✗" for x in places)),
    ]


def core(kw: str) -> str:
    """The keyword without generic words at either end: "best code review skill" -> "code
    review"; "mcp tools for github" stays whole (a phrase keeps its middle)."""
    words = kw.split()
    generic = lambda w: stem(w) in EDGE_GENERIC or w.isdigit()  # noqa: E731
    while words and generic(words[0]):
        words = words[1:]
    while words and generic(words[-1]):
        words = words[:-1]
    return " ".join(words) or kw


def _freshness_check(p: dict, today: date | None = None) -> tuple[str, str, str]:
    """Check title year vs JSON-LD dateModified/lastReviewed & visible review dates."""
    today = today or date.today()
    today_iso = today.isoformat()
    cur_year = today.year
    title_years = [int(y) for y in _YEAR_RE.findall(p["title"] + " " + " ".join(p["h1"]))]
    all_dates = sorted(set(p.get("ld_dates", []) + p.get("vis_dates", [])))
    future = [d for d in all_dates if d > today_iso]
    if future:
        return ("标题年份与更新日期一致", "fail", f"存在未来日期: {', '.join(future)} (今天 {today_iso})")
    if title_years and any(y > cur_year for y in title_years):
        return ("标题年份与更新日期一致", "fail", f"标题含未来年份 {max(title_years)} (当前 {cur_year})")
    if title_years and any(y < cur_year for y in title_years):
        return ("标题年份与更新日期一致", "warn", f"标题含旧年份 {min(title_years)} (当前 {cur_year})")
    if all_dates and title_years:
        latest_year = int(all_dates[-1][:4])
        if latest_year != max(title_years):
            return ("标题年份与更新日期一致", "warn", f"标题 {max(title_years)} vs 页面日期 {all_dates[-1]}")
    detail = f"标题 {max(title_years) if title_years else '无年份'} · 日期 {all_dates[-1] if all_dates else '动态刷新'}"
    return ("标题年份与更新日期一致", "ok", detail)


def _structure_checks(p: dict, url: str, today: date | None = None) -> list[tuple[str, str, str]]:
    """Suski citation-structure metrics + URL/title freshness checks."""
    cells = p.get("table_cells", 0)
    bolds = p.get("bold_spans", 0)
    h2s = p.get("h2", 0)
    first100 = p.get("first_100_text", " ".join(p.get("words", [])[:100]))
    has_bluf = bool(_BLUF_RE.search(first100))
    url_has_year = bool(_URL_YEAR_RE.search(url))
    return [
        ("对比表单元格数", "ok" if cells >= TABLE_CELLS_MIN else "warn" if cells > 0 else "fail",
         f"{cells} 格(目标 ≥{TABLE_CELLS_MIN})"),
        ("加粗 verdict/span 数", "ok" if bolds >= BOLD_MIN else "warn",
         f"{bolds} 处(目标 ≥{BOLD_MIN})"),
        ("H2 数量", "ok" if H2_MIN <= h2s <= H2_MAX else "warn",
         f"{h2s} 个(目标 {H2_MIN}–{H2_MAX}, ~8)"),
        ("首 100 词直答(BLUF)", "ok" if has_bluf else "warn",
         "首屏含肯定句直答" if has_bluf else "首 100 词缺 The best ... is / our pick is 直答"),
        ("URL 不含年份", "fail" if url_has_year else "ok",
         "URL 含年份(换年成死资产)" if url_has_year else url),
        _freshness_check(p, today),
    ]


def _content_checks(p: dict, kw: str) -> list[tuple[str, str, str]]:
    n = len(p["words"])
    rank, top = ngram_rank(p["words"], core(kw))
    return [
        ("关键词在开头 100 词", "ok" if _has(" ".join(p["words"][:100]), kw) else "warn", ""),
        ("正文词数", "fail" if n < WORDS_MIN else "ok" if n <= WORDS_IDEAL else "warn", f"{n} 词"),
        ("词频榜(核心词)", "ok" if rank and rank <= DENSITY_TOP else "warn" if rank and rank <= 10 else "fail",
         f"`{core(kw)}` 第 {rank or '—'} 名;前列:" + "、".join(f"{g}({c})" for g, c in top[:3])),
        ("HTML 体积", "ok" if p["kb"] <= HTML_MAX_KB else "warn", f"{p['kb']} KB"),
        ("结构化数据", "ok" if p["jsonld"] else "warn", f"{p['jsonld']} 段"),
        ("图片 alt/宽高", "ok" if not p["imgs_bad"] else "warn", f"{p['imgs_bad']} 张缺"),
    ]


def checks(p: dict, kw: str, url: str, today: date | None = None) -> list[tuple[str, str, str]]:
    """(name, ok/warn/fail, detail) per check."""
    return _meta_checks(p, kw, url) + _content_checks(p, kw) + _structure_checks(p, url, today)


def score(results: list[tuple[str, str, str]]) -> int:
    points = {"ok": 1.0, "warn": 0.5, "fail": 0.0}
    return round(100 * sum(points[s] for _, s, _ in results) / len(results))


def audit_link(url: str, kw: str) -> str:
    return "https://seo.web.cafe/audit/?" + urllib.parse.urlencode({"url": url, "kw": kw})


def check_page(page: dict, gsc: dict[str, list[tuple[str, int]]]) -> dict:
    url = f"{SITE}/best/{page['slug']}/"
    try:
        parsed = parse(fetch(url.replace(SITE, FETCH_BASE, 1)))
    except OSError as exc:
        return {"slug": page["slug"], "url": url, "error": str(exc)[:120]}
    kw, source = target_keyword(page, parsed["title"], gsc)
    results = checks(parsed, kw, url)
    return {"slug": page["slug"], "url": url, "keyword": kw, "source": source, "score": score(results),
            "results": results, "audit": audit_link(url, kw)}


# --- the report ----------------------------------------------------------------------------

def page_lines(r: dict) -> list[str]:
    if r.get("error"):
        return [f"### /best/{r['slug']}/ — 读取失败:{r['error']}", ""]
    flag = "✅" if r["score"] >= PASS_SCORE else "⚠️"
    lines = [f"### {flag} /best/{r['slug']}/ — {r['score']} 分", "",
             f"目标词 `{r['keyword']}`(来源:{r['source']}) · [哥飞体检]({r['audit']})", "",
             "| 检查 | 结果 | 说明 |", "|---|---|---|"]
    icon = {"ok": "✓", "warn": "!", "fail": "✕"}
    lines += [f"| {n} | {icon[s]} | {d.replace('|', '/')} |" for n, s, d in r["results"] if s != "ok"]
    return lines + (["", "全部通过"] if all(s == "ok" for _, s, _ in r["results"]) else []) + [""]


def report(rows: list[dict], why: str) -> str:
    low = [r for r in rows if r.get("error") or r["score"] < PASS_SCORE]
    head = [f"## 场景页体检:{len(rows)} 页,{len(low)} 页低于 {PASS_SCORE} 分", "", why, "",
            "只列出没通过的项。分数是我们自己的检查,不等于哥飞体检的分数;要看他的完整评分点链接。", ""]
    ordered = sorted(rows, key=lambda r: r.get("score", -1))
    return "\n".join(head + [line for r in ordered for line in page_lines(r)])


def main() -> int:
    out, mode = Path(sys.argv[1]), sys.argv[2]
    live = live_pages()
    if mode == "--changed":
        slugs, why = changed_slugs(sys.argv[3], sys.argv[4]), f"这次部署改动过的页面({sys.argv[3][:7]}..{sys.argv[4][:7]})。"
    elif mode == "--slugs":
        slugs, why = [s for s in sys.argv[3].split(",") if s in live], "指定的页面。"
    else:
        slugs, why = sorted(live), "每周全量体检。"
    if not slugs:
        print("没有改动过的场景页,不出报告")
        return 0
    gsc = gsc_top_queries()
    rows = [check_page(live[s], gsc) for s in slugs]
    out.write_text(report(rows, why))
    print(out.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
