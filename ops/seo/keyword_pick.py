"""The table we pick a scenario page's target keyword from: demand, difficulty, what
ranking first would bring, what the keyword is worth to us, and what page Google wants.

  python ops/seo/keyword_pick.py "claude seo skill" "seo skill" ... [--md out.md] [--json out.json]
  python ops/seo/keyword_pick.py --live-pages [--md out.md]      the seo_keyword of every live page

Columns, all for Google US (AIsa -> DataForSEO, plus one model call):
  volume, KD, intent   Labs keyword overview, one call for all keywords
  traffic potential    Ahrefs' definition on Semrush's data: the monthly organic traffic of the page
                       ranking first, across every query it ranks for. The first page comes from
                       Semrush's own results for the keyword (stable: its database is updated
                       monthly, so two runs agree); its traffic is Semrush's keywords for that URL at
                       position 20 or better, each volume times the click-through rate of its
                       position. When Semrush has nothing for that page, the next one counts and the
                       table says which. A keyword with little volume can sit on a topic worth a lot,
                       and the reverse (熠辉IndieDev's SEO course, 2026-10: Celsius to Fahrenheit, 330K
                       searches, about 2K potential, because Google answers it itself).
                       Three routes failed first, on 2026-10-14: DataForSEO's traffic estimate for a
                       URL (1 visit a month for the top page of a 27K-search keyword); its ranked-
                       keywords tool (not offered through AIsa); and taking the top page from the live
                       result page, which changed between two runs (a GitHub repository, then a
                       YouTube video; once the results of an unrelated query).
  value 0-3            how fully a list of open-source agent skills, MCP servers and plugins with
                       security grades answers the query. A model drafts it from the keyword and
                       the first-page titles and says why; a person can overrule it in
                       ops/seo/keyword-value-overrides.json ({"keyword": [score, "reason"]}).
  first page           what kinds of pages rank: lists, directories, single tools, tutorials,
                       videos, forums, docs, repositories. The 10-11 SERP check showed volume and
                       KD alone pick "find the official one" keywords our list pages cannot win.

Cost seen on 2026-10-14: about $0.04 to $0.06 a keyword (live result page $0.002; Semrush $0.02
for its results and $0.02 for each page it knows; a page it does not know costs nothing), plus one
overview call for the batch.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops/radar"))
import aisa  # noqa: E402

US, ENGLISH = 2840, "en"
OVERVIEW_TOOL = "post_dataforseo_labs_google_keyword_overview_live"
SERP_TOOL = "post_dataforseo_serp_google_organic_live_regular"
PAGE_KEYWORDS_TOOL = "get_semrush_url_organic_keywords"
TOP_PAGES_TOOL = "get_semrush_organic_results"
# Share of clicks by position on a plain results page (averages published by Advanced Web Ranking, 2024).
CTR = {1: .276, 2: .158, 3: .11, 4: .084, 5: .063, 6: .049, 7: .039, 8: .033, 9: .027, 10: .024}
CTR_PAGE_TWO = .01               # positions 11 to 20
COUNTED_POSITIONS = 20
TP_CANDIDATES = 3                # Semrush's first results tried, in order, until it knows one
WORKERS = 4
UNDERSTATED_SHARE = 0.25
UNDERSTATED_MIN_VOLUME = 100
VALUE_MODELS = ("claude-sonnet-4-6", "gpt-4.1-mini")
OVERRIDES = ROOT / "ops/seo/keyword-value-overrides.json"
KEYWORDS = ROOT / "frontend/scripts/scenario-keywords.json"
TOP = 10
SHOWN_TITLES = 6

DIRECTORIES = {"mcp.so", "mcpmarket.com", "glama.ai", "pulsemcp.com", "smithery.ai", "mcpservers.org", "skillsmp.com",
               "skills.sh", "lobehub.com", "toolify.ai", "futurepedia.io", "theresanaiforthat.com", "mcp.directory",
               "awesomeskill.ai", "skillsllm.com", "claudemarketplaces.com", "agentskillshub.top", "producthunt.com",
               "alternativeto.net", "saashub.com", "mcpserver.so", "ubos.tech", "mcpbundles.com"}
FORUMS = {"reddit.com", "quora.com", "news.ycombinator.com", "stackoverflow.com", "linkedin.com"}
LIST = re.compile(r"\b(?:\d+\s+(?:best|top|free)|best|top \d+|\d+ (?:\w+ ){0,3}(?:tools|skills|servers|apps|plugins|"
                  r"alternatives|mcps?))\b|\balternatives\b|\bcompared\b| vs\.? ", re.I)
TUTORIAL = re.compile(r"\bhow to\b|\bguide\b|\btutorial\b|\bstep[- ]by[- ]step\b|\bsetup\b|\bset up\b", re.I)
FORM_ORDER = ("list", "directory", "repository", "tool or product", "tutorial", "video", "forum", "docs")
FORM_ZH = {"list": "榜单", "directory": "目录", "repository": "仓库", "tool or product": "单个工具", "tutorial": "教程",
           "video": "视频", "forum": "论坛", "docs": "文档"}
VALUE_SYSTEM = """You score search keywords for Agent Skills Hub, a site whose pages are lists of
open-source AI agent skills, MCP servers and Claude Code / Codex plugins for one task, each
security-graded. Score how fully such a page answers the searcher, 0 to 3:
3 = the searcher wants to find or compare open-source agent skills, MCP servers or plugins for a task;
    a graded list answers it completely.
2 = a list page is one good answer among others: the first page mixes products and open-source tools,
    or the searcher wants one specific tool that such a list includes.
1 = the audience overlaps but the searcher wants something else: a commercial product, a tutorial,
    news, a definition, the official page of one brand.
0 = unrelated to agent skills and tools.
Use the first-page titles as evidence of what the searcher wants. Reply with JSON only:
[{"keyword": "...", "value": 0-3, "reason": "under 20 words"}]"""


def domain(url: str) -> str:
    host = re.sub(r"^https?://", "", url or "").split("/")[0].lower()
    return host.removeprefix("www.")


def form_of(item: dict) -> str:
    """What kind of page one organic result is."""
    host, title = domain(item.get("url", "")), item.get("title") or ""
    rules = ((host.endswith("youtube.com"), "video"), (host in FORUMS or host.endswith("reddit.com"), "forum"),
             (host == "github.com", "repository"), (host in DIRECTORIES, "directory"), (bool(LIST.search(title)), "list"),
             (bool(TUTORIAL.search(title)), "tutorial"), (host.startswith(("docs.", "developers.", "support.", "help.")), "docs"))
    return next((name for hit, name in rules if hit), "tool or product")


def form_summary(items: list[dict]) -> str:
    counts = {}
    for item in items[:TOP]:
        counts[form_of(item)] = counts.get(form_of(item), 0) + 1
    return " · ".join(f"{FORM_ZH[f]} {counts[f]}" for f in FORM_ORDER if f in counts)


def overview(keywords: list[str]) -> tuple[dict[str, dict], int]:
    data, cost = aisa.call([{"call_id": "o", "tool": OVERVIEW_TOOL, "arguments": {"body": [{
        "keywords": keywords, "location_code": US, "language_code": ENGLISH}]}}])
    task = ((data.get("o") or {}).get("tasks") or [{}])[0]
    items = ((task.get("result") or [{}])[0] or {}).get("items") or []
    return {i["keyword"]: {"volume": (i.get("keyword_info") or {}).get("search_volume"),
                           "kd": (i.get("keyword_properties") or {}).get("keyword_difficulty"),
                           "intent": (i.get("search_intent_info") or {}).get("main_intent")} for i in items}, cost


def first_pages(keywords: list[str]) -> tuple[dict[str, list[dict]], int]:
    calls = [{"call_id": f"s{i}", "tool": SERP_TOOL, "arguments": {"body": [{
        "keyword": k, "location_code": US, "language_code": ENGLISH, "depth": TOP}]}} for i, k in enumerate(keywords)]
    data, cost = aisa.call_all(calls)
    pages = {}
    for i, k in enumerate(keywords):
        task = ((data.get(f"s{i}") or {}).get("tasks") or [{}])[0]
        items = ((task.get("result") or [{}])[0] or {}).get("items") or []
        pages[k] = [{"url": x.get("url"), "title": x.get("title"), "rank": x.get("rank_group")}
                    for x in items if x.get("type") == "organic"]
    return pages, cost


def page_traffic(text: str) -> int | None:
    """Semrush's "Keyword;Position;Search Volume;CPC" rows -> estimated monthly visits; None when
    Semrush has nothing for the page ("ERROR 50 :: NOTHING FOUND")."""
    lines = [l.split(";") for l in (text or "").strip().splitlines()]
    if not lines or not lines[0] or lines[0][0].startswith("ERROR"):
        return None
    total = 0.0
    for row in lines[1:]:
        if len(row) >= 3 and row[1].isdigit() and row[2].isdigit() and int(row[1]) <= COUNTED_POSITIONS:
            total += int(row[2]) * CTR.get(int(row[1]), CTR_PAGE_TWO)
    return round(total)


def semrush_top(keyword: str) -> tuple[list[str], int]:
    """The URLs Semrush has ranking for `keyword` (US), best first."""
    data, cost = aisa.call([{"call_id": "p", "tool": TOP_PAGES_TOOL, "arguments": {"phrase": keyword, "database": "us"}}])
    text = data.get("p") if isinstance(data.get("p"), str) else ""
    rows = [l.split(";") for l in text.strip().splitlines()[1:]]
    return [r[1] for r in rows if len(r) > 1 and r[1].startswith("http")], cost


def potential(urls: list[str]) -> tuple[dict, int]:
    """({"tp", "tp_page", "tp_rank"}, cost) from the first of `urls` Semrush has data for."""
    cost = 0
    for rank, url in enumerate(urls[:TP_CANDIDATES], 1):
        data, spent = aisa.call([{"call_id": "u", "tool": PAGE_KEYWORDS_TOOL, "arguments": {"url": url, "database": "us"}}])
        cost += spent
        tp = page_traffic(data.get("u") if isinstance(data.get("u"), str) else "")
        if tp is not None:
            return {"tp": tp, "tp_page": url, "tp_rank": rank}, cost
    return {"tp": None, "tp_page": "", "tp_rank": None}, cost


def potentials(rows: list[dict]) -> tuple[dict[str, dict], int, list[str]]:
    from concurrent.futures import ThreadPoolExecutor
    def one(r):
        try:
            urls, cost = semrush_top(r["keyword"])
            found, more = potential(urls)
            return r["keyword"], found, cost + more, ""
        except aisa.AisaError as exc:
            return r["keyword"], {"tp": None, "tp_page": "", "tp_rank": None}, 0, f"traffic potential, {r['keyword']}: {exc}"
    with ThreadPoolExecutor(WORKERS) as pool:
        done = list(pool.map(one, rows))
    return {k: v for k, v, _, _ in done}, sum(c for _, _, c, _ in done), [e for *_, e in done if e]


def value_prompt(rows: list[dict]) -> str:
    lines = []
    for r in rows:
        titles = "; ".join(f"{domain(p['url'])}: {p['title']}" for p in r["first_page"][:SHOWN_TITLES])
        lines.append(f"- {r['keyword']} | first page: {titles or 'unknown'}")
    return "\n".join(lines)


def parse_values(text: str) -> dict[str, tuple[int, str]]:
    match = re.search(r"\[.*\]", text, re.S)
    try:
        rows = json.loads(match.group(0)) if match else []
    except ValueError:
        return {}
    return {r["keyword"]: (int(r["value"]), r.get("reason", "")) for r in rows
            if isinstance(r, dict) and str(r.get("value", "")).isdigit() and 0 <= int(r["value"]) <= 3}


def values(rows: list[dict]) -> tuple[dict[str, tuple[int, str]], str]:
    """(keyword -> (score, reason), the model used). Overrides win over the model."""
    found, used = {}, ""
    for model in VALUE_MODELS:
        try:
            found, used = parse_values(aisa.chat(model, VALUE_SYSTEM, value_prompt(rows), max_tokens=2000)), model
        except aisa.AisaError:
            continue
        if found:
            break
    held = json.loads(OVERRIDES.read_text()) if OVERRIDES.exists() else {}
    found.update({k: (int(v[0]), f"{v[1]} (owner)") for k, v in held.items()})
    return found, used


def pick(keywords: list[str]) -> dict:
    """{"rows": [...], "cost": micro-USD, "model": str, "errors": [...]}"""
    rows, cost, errors = [{"keyword": k} for k in keywords], 0, []
    steps = (("overview", lambda: overview(keywords)), ("first page", lambda: first_pages(keywords)))
    got = {}
    for name, step in steps:
        try:
            got[name], spent = step()
            cost += spent
        except aisa.AisaError as exc:
            got[name] = {}
            errors.append(f"{name}: {exc}")
    for r in rows:
        r.update(got["overview"].get(r["keyword"], {}))
        r["first_page"] = got["first page"].get(r["keyword"], [])
        r["first"] = r["first_page"][0]["url"] if r["first_page"] else ""
        r["form"] = form_summary(r["first_page"])
    return finish(rows, cost, errors)


def finish(rows: list[dict], cost: int, errors: list[str]) -> dict:
    tp, spent, failed = potentials(rows)
    cost, errors = cost + spent, errors + failed
    scored, model = values(rows)
    for r in rows:
        found = tp.get(r["keyword"]) or {}
        r["traffic_potential"], r["tp_page"], r["tp_rank"] = found.get("tp"), found.get("tp_page", ""), found.get("tp_rank")
        r["value"], r["value_reason"] = scored.get(r["keyword"], (None, ""))
    rows.sort(key=lambda r: (-(r["value"] if r["value"] is not None else -1), -(r["traffic_potential"] or 0)))
    return {"rows": rows, "cost": cost, "model": model, "errors": errors}


def understated(row: dict) -> bool:
    """The page's estimate is under a quarter of what the keyword alone would bring at #1: Semrush has
    that page ranking low, so the number says more about Semrush's data than about the topic."""
    tp, volume = row.get("traffic_potential"), row.get("volume") or 0
    return tp is not None and volume >= UNDERSTATED_MIN_VOLUME and tp < volume * CTR[1] * UNDERSTATED_SHARE


def num(value) -> str:
    return "–" if value is None else f"{value:,}" if isinstance(value, int) else str(value)


def markdown(result: dict) -> str:
    lines = ["| 词 | 月搜 | KD | 意图 | 流量潜力 | 业务价值 | 前 10 名（实时） | 潜力按这一页 | 价值理由 |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in result["rows"]:
        tp = num(r.get("traffic_potential")) + (f"（第 {r['tp_rank']} 名）" if r.get("tp_rank") and r["tp_rank"] > 1 else "")
        tp += " ⚠" if understated(r) else ""
        lines.append(f"| {r['keyword']} | {num(r.get('volume'))} | {num(r.get('kd'))} | {r.get('intent') or '–'} | "
                     f"{tp} | {num(r.get('value'))} | {r.get('form') or '–'} | "
                     f"{domain(r.get('tp_page', '')) or '–'} | {r.get('value_reason') or ''} |")
    notes = ["流量潜力 = Semrush 里这个词排第一的页面在美国的月自然流量估算：该网址排进前 20 的词，搜索量 × 该位置点击率，"
             "加总（Ahrefs 的定义，换成 Semrush 的数据）。Semrush 没有第一名的数据时用下一名，表里注明第几名。"
             "⚠ = 不到「月搜 × 第一名点击率」的四分之一：Semrush 对这页的数据少，只能当下限看。"
             "「前 10 名（实时）」来自 DataForSEO 的实时结果，只用来看页面形态和判断业务价值。",
             f"业务价值 0–3 由 {result['model'] or '模型'} 根据词和首页标题起草，可在 ops/seo/keyword-value-overrides.json 里改。"
             f"本次 ${result['cost'] / 1e6:.3f}。"]
    notes += [f"失败：{e}" for e in result["errors"]]
    return "\n".join(lines + [""] + notes)


def live_targets() -> list[str]:
    pages = json.loads(KEYWORDS.read_text())
    return sorted({p["seo_keyword"] for p in pages if p.get("seo_keyword") and not p.get("retired")})


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("keywords", nargs="*")
    p.add_argument("--live-pages", action="store_true", help="the seo_keyword of every live scenario page")
    p.add_argument("--md")
    p.add_argument("--json")
    args = p.parse_args()
    keywords = live_targets() if args.live_pages else [" ".join(k.lower().split()) for k in args.keywords]
    if not keywords:
        p.error("give keywords or --live-pages")
    result = pick(keywords)
    text = markdown(result)
    if args.md:
        Path(args.md).write_text(text + "\n")
    if args.json:
        Path(args.json).write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
