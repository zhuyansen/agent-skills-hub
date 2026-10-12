"""The generic terms behind the names: what people do with a new thing, as search terms.

A name ("SynthID Detector") has a short life as a keyword and belongs to someone. The
job it does ("ai image detector") is what people keep searching, and nobody owns it.
For the day's new names this step:

  1. collects evidence: popular posts that mention the name (AIsa, X advanced search)
     and, for a repository, its README;
  2. asks a model which jobs the evidence shows people doing, and the keyword an
     ordinary person would type for each job. A phrase built on another product's name
     ("photoshop alternative") is kept and marked `brand`: demand often hangs on the
     incumbent, and that is yours to weigh;
  3. looks the phrases up: Google Ads monthly searches (one batch call);
  4. reads Google Trends for the names and for the phrases with enough volume, twice
     each: alone, for the shape of the curve (when it started rising, its peak, what it
     is doing now), and next to a benchmark keyword ("gpts" by default), for the size.
     A generic term's searches a day come from its own Google Ads volume, moved to today
     along its own curve. The benchmark is sized from those terms, and a name, which has
     no volume data yet, is sized against the benchmark.

The result is one table, names and generic terms together, each with a decision
(table()). Phrases with measurable volume are also kept as leads of kind "usecase" and
go through the same 14-day review as the names.

What it cannot do: on the day a model is announced the posts are announcements, and
no job shows yet; each name is therefore read twice, the day it appears and
`recheck_days` later. Google Ads volumes run about two months behind, so they tell how
big a need is, not whether this release moved it; Trends tells that, but reads nothing
for terms under a few hundred searches a month. Most proposed phrases have no volume.

Costs seen in October 2026: $0.003 per name for the posts, $0.09 for the volume batch
(up to 1,000 phrases), $0.0012 per Trends lookup (two per row of the table), plus the model's tokens.

The same module as github.com/zhuyansen/new-term-radar (radar/usecases.py), with this
repo's flat imports, its settings as constants, and the table in Chinese (table()).
"""
from __future__ import annotations

import base64
import json
import os
import re
import statistics
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import gzip

import aisa
import review

POSTS_KEPT = 12
POST_CHARS = 400
README_CHARS = 3000
MIN_FAVES = 50
SEARCH_DAYS = 14
TRENDS_DAYS, RECENT_DAYS = 90, 7
RISE_WINDOW = 30           # a rise counts when it happened in the last 30 days
RISE_DAYS = 2              # and lasted at least two days
NOW_DAYS = 3               # a peak in the last three settled days is still rising
HOLD_SHARE = 0.5           # at half its peak or more in those days, a term is holding
CALIBRATE_MIN = 1000       # monthly searches a term needs to help size the benchmark
NEW_BASE_MAX = 10          # a baseline under 10 (of 100) means the term barely existed before
MAX_PER_NAME = 6
STATE_DAYS = 30
SEARCH_TOOL = "get_twitter_tweet_advanced_search"
VOLUME_TOOL = "post_dataforseo_keywords_gads_search_volume_live"
UA = "agentskillshub-radar/1.0"
SETTINGS = {"per_day": 5, "model": "claude-sonnet-4-6", "min_volume": 50, "trends_max": 10, "recheck_days": 3,
            "location_code": 2840, "benchmark": "gpts", "min_daily": 300}
SYSTEM = (
    "You help an SEO researcher who builds tool pages around new AI releases. You get the NAME of a new model, product "
    "or repository and EVIDENCE: popular posts about it and, for a repository, its README.\n"
    "Step 1: work out the concrete jobs people are doing with it, according to the evidence.\n"
    "Step 2: for each job, write the KEYWORD a keyword tool would list for it: the short head term people type into "
    "Google when they want that job done and have never heard of this product.\n"
    "A keyword is a noun phrase for a tool or a task, 2 to 4 words, lowercase: 'ai image detector', 'psd editor online', "
    "'run llm locally', 'photo to anime', 'ai dance video generator', 'remove background from video'. Not a sentence, "
    "not a feature description ('generate ultra detailed images', 'combine multiple reference images'), not a quality "
    "('fast image generation'), not news.\n"
    "Never use the NAME itself or the name of its maker. Prefer keywords with no names at all. When the evidence shows "
    "people comparing it to an established product or using it on a named platform, you may add up to two keywords "
    "built on that established name ('photoshop alternative', 'debloat macos') and set `brand` to true for them. Set "
    "`brand` to true for any keyword that contains a brand, product, company, operating system, person, studio, "
    "franchise or character name; false otherwise.\n"
    "Every keyword needs a short quote from the evidence showing people doing that job. No evidence of a concrete job "
    "(only an announcement, prices or benchmarks): return an empty list. Do not guess.\n"
    "Answer with JSON only: {\"what_it_is\": \"one sentence\", \"use_cases\": [{\"phrase\": \"...\", \"evidence\": "
    "\"short quote\", \"brand\": false}]}, at most 6, the most specific job first."
)


def due(names: list[str], seen: dict[str, dict], today: date, per_day: int, recheck_days: int) -> list[str]:
    """Names to read today: new ones first, then those read once `recheck_days` ago or earlier."""
    new = [n for n in names if n not in seen]
    cutoff = (today - timedelta(days=recheck_days)).isoformat()
    again = sorted((n for n, s in seen.items() if s["runs"] == 1 and s["first"] <= cutoff), key=lambda n: seen[n]["first"])
    return list(dict.fromkeys(new + again))[:per_day]


def _readme(repo: str) -> str:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": UA}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    try:
        with urllib.request.urlopen(urllib.request.Request(f"https://api.github.com/repos/{repo}/readme", headers=headers), timeout=30) as res:
            return base64.b64decode(json.load(res)["content"]).decode("utf-8", "replace")[:README_CHARS]
    except (OSError, KeyError, ValueError):
        return ""


def evidence(names: list[str], repos: dict[str, str], today: date) -> tuple[dict[str, dict], int]:
    """{name: {"posts": [...], "readme": str}} and the cost in micro-USD."""
    since = (today - timedelta(days=SEARCH_DAYS)).isoformat()
    calls = [{"call_id": f"n{i}", "tool": SEARCH_TOOL, "arguments": {
        "query": f'"{n}" min_faves:{MIN_FAVES} -filter:replies since:{since}', "queryType": "Top"}} for i, n in enumerate(names)]
    data, cost = aisa.call_all(calls)
    out = {}
    for i, n in enumerate(names):
        d = data.get(f"n{i}") or {}
        tweets = d.get("tweets") or (d.get("data") or {}).get("tweets") or []
        posts = sorted(({"text": " ".join((t.get("text") or "").split()), "likes": int(t.get("likeCount") or 0),
                         "by": (t.get("author") or {}).get("userName") or "?", "url": t.get("url", "")} for t in tweets),
                       key=lambda p: -p["likes"])[:POSTS_KEPT]
        out[n] = {"posts": posts, "readme": _readme(repos[n]) if repos.get(n) else "", "repo": repos.get(n, "")}
    return out, cost


def parse(answer: str, name: str) -> list[dict]:
    """The model's use cases, cleaned: lowercased, 2 to 5 words, never the name itself, no repeats."""
    m = re.search(r"\{.*\}", answer, re.S)
    try:
        items = json.loads(m.group(0)).get("use_cases", []) if m else []
    except (ValueError, AttributeError):
        return []
    out, seen = [], set()
    for it in items if isinstance(items, list) else []:
        phrase = " ".join(str(it.get("phrase", "")).lower().split()) if isinstance(it, dict) else ""
        if not 2 <= len(phrase.split()) <= 5 or name in phrase or phrase in seen:
            continue
        seen.add(phrase)
        out.append({"phrase": phrase, "evidence": " ".join(str(it.get("evidence", "")).split())[:160], "brand": bool(it.get("brand"))})
    return out[:MAX_PER_NAME]


def propose(model: str, name: str, ev: dict) -> list[dict]:
    if not ev["posts"] and not ev["readme"]:
        return []
    posts = "\n".join(f"- ({p['likes']} likes) @{p['by']}: {p['text'][:POST_CHARS]}" for p in ev["posts"])
    user = f"NAME: {name}\n\nPOSTS:\n{posts or '(none found)'}\n" + (f"\nREADME of {ev['repo']}:\n{ev['readme']}\n" if ev["readme"] else "")
    return parse(aisa.chat(model, SYSTEM, user, max_tokens=900), name)


def volumes(phrases: list[str], location_code: int) -> tuple[dict[str, dict], int]:
    """{phrase: {"volume", "month"}} from Google Ads, one batch call."""
    if not phrases:
        return {}, 0
    data, cost = aisa.call([{"call_id": "vol", "tool": VOLUME_TOOL, "arguments": {"body": [{
        "keywords": phrases, "location_code": location_code, "language_code": "en"}]}}])
    out = {}
    for r in ((data.get("vol") or {}).get("tasks") or [{}])[0].get("result") or []:
        ms = r.get("monthly_searches") or []
        out[r["keyword"]] = {"volume": int(r.get("search_volume") or 0),
                             "month": f"{ms[0]['year']}-{ms[0]['month']:02d}" if ms else ""}
    return out, cost


def shape(points: list[tuple[date, int]], today: date) -> dict:
    """What a term's own Trends curve says: is it new, when did it start rising, where is
    the peak, what is it doing now. `points` is the daily series on its own 0-100 scale;
    its unsettled last days are dropped, and "now" means the last settled days. A rise is
    judged inside the last RISE_WINDOW days against the level before them, so an old peak
    does not count, and it needs RISE_DAYS days above the line: a term with few searches
    shows single-day spikes out of nothing ("debloat macos": 0, 0, 100, 0, 0)."""
    points = review.settled(points, today)
    top = max((v for _, v in points), default=0)
    if not top:
        return {"no_data": True}
    # Back onto 0-100: when a dropped day held the series' 100, the real days sit squeezed
    # under 10 and no threshold in points would mean anything.
    points = [(d, round(v * 100 / top)) for d, v in points]
    end = points[-1][0]
    cut = end - timedelta(days=RISE_WINDOW)
    old = [v for d, v in points if d < cut]
    window = [(d, v) for d, v in points if d >= cut]
    base = statistics.mean(old) if old else 0.0
    peak_day, peak = max(window, key=lambda p: (p[1], p[0]))
    line = max(base * review.RISE_FACTOR, base + review.RISE_MIN)
    above = [d for d, v in window if v >= line]
    rose = len(above) >= RISE_DAYS
    out = {"no_data": False, "base": round(base, 1), "peak": peak, "peak_day": peak_day.isoformat(),
           "rose": rose, "new": rose and base < NEW_BASE_MAX}
    if not rose:
        return {**out, "now": "flat"}
    out["started"] = above[0].isoformat()
    latest = max(v for d, v in window if d > end - timedelta(days=NOW_DAYS))
    out["now"] = "rising" if (end - peak_day).days < NOW_DAYS else "holding" if latest >= HOLD_SHARE * peak else "fading"
    return out


def _mean(values: list[int]) -> float:
    return statistics.mean(values) if values else 0.0


def _in_month(day: date, month: str) -> bool:
    return day.isoformat().startswith(month)


def own_per_day(points: list[tuple[date, int]], volume: int, month: str, today: date) -> int | None:
    """Searches a day now, from the term's own numbers: its Google Ads volume for `month`
    scaled by how its Trends level in the last RECENT_DAYS compares with that month."""
    points = review.settled(points, today)
    anchor = _mean([v for d, v in points if _in_month(d, month)])
    recent = _mean([v for _, v in points[-RECENT_DAYS:]])
    return round(volume / 30 * recent / anchor) if anchor and volume else None


def bench_daily(rows: list[dict]) -> float | None:
    """The benchmark's searches a day, worked back from the terms whose volume is known:
    in the month of the volume data, a term at a third of the benchmark's level with
    3,000 searches a day puts the benchmark at 9,000. The median over the terms with
    at least CALIBRATE_MIN searches a month; Trends is too coarse below that."""
    found = []
    for r in rows:
        pair, month = r.get("_pair") or [], r.get("month")
        if not month or r.get("volume", 0) < CALIBRATE_MIN:
            continue
        term = _mean([v for d, v, _ in pair if _in_month(d, month)])
        bench = _mean([b for d, _, b in pair if _in_month(d, month)])
        if term and bench:
            found.append(r["volume"] / 30 * bench / term)
    return statistics.median(found) if found else None


def size(pair: list[tuple[date, int, int]], today: date, daily: float | None) -> dict:
    """A term next to the benchmark on one scale: its peak against the benchmark's usual
    level, and, when the benchmark's size is known, searches a day now."""
    pair = review.settled(pair, today)
    level = _mean([b for _, _, b in pair])
    if not level:
        return {}
    window = pair[-RISE_WINDOW:]
    out = {"peak_vs": max(v for _, v, _ in window), "bench_level": round(level, 1)}
    if daily:
        out["per_day"] = round(_mean([v for _, v, _ in pair[-RECENT_DAYS:]]) / level * daily)
    return out


def decide(s: dict, per_day: int | None, min_daily: int) -> str:
    """prioritize: rose, still up, and big enough. watch: rose but small; too early to
    read; or a term that did not move but has steady demand of that size (a need the
    new thing serves, not one it created). skip: fading, or flat and small."""
    big = (per_day or 0) >= min_daily
    if s.get("no_data"):
        return "watch"
    if s["now"] == "fading":
        return "skip"
    if s["now"] == "flat":
        return "watch" if big else "skip"
    return "prioritize" if big else "watch"


def _pairs(task: dict) -> list[tuple[date, int, int]]:
    try:
        item = task["result"][0]["items"][0]
    except (KeyError, IndexError, TypeError):
        return []
    rows = []
    for p in item.get("data", []):
        v = (p.get("values") or []) + [0, 0]
        rows.append((date.fromisoformat(p["date_from"]), int(v[0] or 0), int(v[1] or 0)))
    return rows


def fetch_series(keywords: list[str], benchmark: str, today: date) -> tuple[dict[str, dict], int]:
    """{keyword: {"solo": [(day, value)], "pair": [(day, value, benchmark value)]}}: two Trends lookups each."""
    window = {"date_from": (today - timedelta(days=TRENDS_DAYS)).isoformat(), "date_to": today.isoformat()}
    calls = []
    for i, k in enumerate(keywords):
        calls.append({"call_id": f"s{i}", "tool": review.TOOL, "arguments": {"body": [{"keywords": [k], **window}]}})
        calls.append({"call_id": f"p{i}", "tool": review.TOOL, "arguments": {"body": [{"keywords": [k, benchmark], **window}]}})
    data, cost = aisa.call_all(calls)
    task = lambda cid: ((data.get(cid) or {}).get("tasks") or [{}])[0]  # noqa: E731
    return {k: {"solo": review._series(task(f"s{i}")), "pair": _pairs(task(f"p{i}"))} for i, k in enumerate(keywords)}, cost


def measure(rows: list[dict], series: dict[str, dict], min_daily: int, today: date) -> float | None:
    """Fills each row with its shape, size and decision. Returns the benchmark's calibrated size."""
    for r in rows:
        r["_pair"] = series.get(r["phrase"], {}).get("pair") or []
    daily = bench_daily(rows)
    for r in rows:
        solo = series.get(r["phrase"], {}).get("solo") or []
        s, z = shape(solo, today), size(r.pop("_pair"), today, daily)
        own = own_per_day(solo, r.get("volume", 0), r.get("month", ""), today)
        if own is not None:
            z["per_day"] = own      # a term's own volume is a better anchor than the benchmark
        r.update({**s, **z, "decision": decide(s, z.get("per_day"), min_daily)})
    return daily


def run(state: Path, names: list[str], repos: dict[str, str], today: date | None = None) -> dict:
    """names: today's named leads, most important first. repos: {name: "owner/repo"} where known."""
    c = SETTINGS
    today = today or date.today()
    path = state / "usecases.json.gz"
    seen: dict[str, dict] = json.loads(gzip.decompress(path.read_bytes())) if path.exists() else {}
    todo = due(names, seen, today, c["per_day"], c["recheck_days"])
    if not todo:
        return {"names": [], "rows": [], "proposed": 0, "cost_micros": 0}
    ev, cost = evidence(todo, repos, today)
    proposed: dict[str, dict] = {}
    for name in todo:
        for u in propose(c["model"], name, ev[name]):
            row = proposed.setdefault(u["phrase"], {**u, "term": u["phrase"], "kind": "generic", "names": []})
            row["names"].append(name)
            row["brand"] |= u["brand"]
    bench = c["benchmark"].lower()
    vol, c2 = volumes(sorted(proposed), c["location_code"])
    generic = sorted((dict(r, **vol[p]) for p, r in proposed.items() if vol.get(p, {}).get("volume", 0) >= c["min_volume"]),
                     key=lambda r: -r["volume"])[:c["trends_max"]]
    rows = [{"term": n, "phrase": n, "kind": "name", "names": [], "brand": True, "evidence": "", **vol.get(n, {})} for n in todo] + generic
    series, c3 = fetch_series([r["phrase"] for r in rows], bench, today)
    daily = measure(rows, series, c["min_daily"], today)
    order = {"prioritize": 0, "watch": 1, "skip": 2}
    rows.sort(key=lambda r: (order[r["decision"]], -(r.get("per_day") or 0), -(r.get("volume") or 0)))
    for name in todo:
        s = seen.setdefault(name, {"first": today.isoformat(), "runs": 0})
        s["runs"] += 1
    cutoff = (today - timedelta(days=STATE_DAYS)).isoformat()
    path.write_bytes(gzip.compress(json.dumps({n: s for n, s in seen.items() if s["first"] >= cutoff}).encode()))
    return {"names": todo, "rows": rows, "proposed": len(proposed), "kept": len(generic), "benchmark": bench,
            "bench_daily": round(daily) if daily else None, "volume_month": next((r["month"] for r in generic if r.get("month")), ""),
            "no_evidence": [n for n in todo if not ev[n]["posts"] and not ev[n]["readme"]],
            "cost_micros": cost + c2 + c3}


NOW_ZH = {"rising": "还在涨", "holding": "维持", "fading": "回落", "flat": "没动"}
DECISION_ZH = {"prioritize": "**优先**", "watch": "观察", "skip": "跳过"}


def _row(r: dict) -> str:
    generic, none = r["kind"] == "generic", r.get("no_data")
    peak = f"{r['peak_vs']} vs {r['bench_level']}" if "peak_vs" in r else "—"
    return (f"| **{r['phrase']}**{' ⚠' if generic and r['brand'] else ''} | {'通用词' if generic else '名字'} | "
            f"{', '.join(r['names']) or '—'} | {'—' if none else '是' if r['new'] else '否'} | {r.get('per_day', '—')} | "
            f"{r.get('started') or '—'} | {peak} | {'—' if none else r['peak_day']} | "
            f"{'还读不出' if none else NOW_ZH[r['now']]} | {DECISION_ZH[r['decision']]} |")


def table(uc: dict) -> list[str]:
    """The report section: one table, names and generic terms together."""
    lines = ["", "### 新词表:新名字和它背后的通用词", ""]
    if uc.get("skipped") or uc.get("error"):
        return lines + [uc.get("error") or "跳过"]
    if not uc.get("names"):
        return lines + ["今天没有要读的名字:没有新名字,也没有到第二次阅读时间的。"]
    c = SETTINGS
    bench = f"名字对比基准词 `{uc['benchmark']}`(按今天这批词反推,约每天 {uc['bench_daily']} 次)" if uc.get("bench_daily") \
        else f"今天没法校准基准词 `{uc['benchmark']}`,所以名字没有估算值"
    lines += [f"今天读了:{', '.join(uc['names'])}。提出 {uc['proposed']} 个通用写法,其中 {uc['kept']} 个月搜不低于 {c['min_volume']}"
              f"({uc['volume_month'] or '?'} 数据)。日搜是估算:通用词用它自己的月搜索量沿 Trends 曲线推到现在;{bench}。", "",
              f"| 关键词 | 类型 | 来自 | 新词? | 估算日搜 | 开始上涨 | 峰值 vs {uc['benchmark']} | 峰值日 | 现在 | 决策 |", "|---|---|---|---|---|---|---|---|---|---|"]
    lines += [_row(r) for r in uc["rows"]]
    lines += ["", f"决策规则:优先 = 近 30 天涨过、现在还在高位、估算日搜不低于 {c['min_daily']}。观察 = 涨了但规模小;还太早读不出;"
              "或者没动但本身就有这个规模的稳定需求。跳过 = 已回落,或没动且规模小。Trends 最后两天的数据还没结算,不计入。"]
    if any(r["kind"] == "generic" and r["brand"] for r in uc["rows"]):
        lines.append("⚠ = 这个词带着别人的品牌或产品名,法务和定位风险需要自己判断。")
    said = [f"- **{r['phrase']}**({', '.join(r['names'])}):“{r['evidence'].replace('|', '/')}”"
            for r in uc["rows"] if r["kind"] == "generic" and r["evidence"]]
    if said:
        lines += ["", "原话(每个通用词的依据):", *said]
    if uc.get("no_evidence"):
        lines += ["", f"没找到帖子或 README:{', '.join(uc['no_evidence'])}。"]
    return lines


def leads(uc: dict) -> list[dict]:
    """The generic terms as rows for radar_leads, reviewed after 14 days like the names."""
    return [{"term": r["phrase"], "kinds": ["usecase"], "variants": [r["phrase"]],
             "signals": [f"{', '.join(r['names'])} 背后的通用词,月搜 {r.get('volume', 0)}"]}
            for r in uc.get("rows", []) if r["kind"] == "generic"]
