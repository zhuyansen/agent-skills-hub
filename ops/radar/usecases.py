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
  2b. with a GoAnyAPI key (optional), also takes Google Trends' related queries for the
     name: what people really searched together with it. Queries that hold the name are
     its long-tails ("photocraft download"); the others join the phrases; those that are
     themselves names of other new things ("gpt image 2.5" beside "nano banana 2.1") are
     handed back as leads of kind "cosearch". With that key the names and the bigger
     generic terms also take their shape from a 30-day series for one country, which is
     settled to yesterday and shows moves the worldwide series flattens;
  3. screens them: a second call scores how well the name answers each phrase, and the
     loosely related ones are dropped (a keyword taken from a passing comparison);
  4. looks the rest up: Google Ads monthly searches (one batch call);
  5. reads Google Trends for the names and for the phrases with enough volume, twice
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
import goanyapi
import review

POSTS_KEPT = 12
POST_CHARS = 400
README_CHARS = 3000
MIN_FAVES = 50
SEARCH_DAYS = 14
TRENDS_DAYS, RECENT_DAYS = 90, 7
MOMENTUM_MIN_BASE = 5      # of 100: the week before must reach this for a week-on-week ratio
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
            "location_code": 2840, "benchmark": "gpts", "min_daily": 300, "related": True, "related_geo": "US",
            "country_trends": True, "country_min_volume": 1000, "country_max": 8}
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


SCREEN = (
    "You check keyword candidates for an SEO researcher. NAME is a new model, product or repository; EVIDENCE is what "
    "people posted about it. For each candidate keyword give three things.\n"
    "`score`, 0.0 to 1.0: how well NAME answers that search. Would someone who typed the keyword be served by a page "
    "about using NAME for it? High: the keyword names the main job NAME does, as the evidence shows it ('ai image "
    "detector' for a tool that tells whether an image is AI-made; 'photoshop alternative' for a free clone of that "
    "editor). Low: a side mention, a comparison someone made in passing ('chatgpt alternative' because one post "
    "compared two models), a broad category NAME is only one of thousands in ('ai coding assistant' for a general "
    "language model), or a job the evidence does not show.\n"
    "`brand`, true or false: the keyword contains a brand, product, company, operating system, person, studio, "
    "franchise or character name ('photoshop alternative', 'free up mac disk space').\n"
    "`name`, true or false: the keyword is itself the name of another specific product, model or tool, with or "
    "without its maker ('gpt image 2.5', 'gemini 4 argon', 'mistral large 4'), not a task or a kind of tool.\n"
    "Answer with JSON only, one object per candidate, in the same order: "
    "[{\"i\": 0, \"score\": 0.9, \"brand\": false, \"name\": false}, ...]"
)
RELEVANT_MIN = 0.6
RELATED_KEPT = 12          # related queries per name that go to the screen
COSEARCH_KEPT = 5          # other names kept as leads per name


def split_related(name: str, related: dict[str, list[str]]) -> tuple[list[str], list[dict]]:
    """Related queries sorted into the name's own long-tails ("photocraft download") and
    candidate phrases. One-word queries ("github", "google") say nothing and are dropped."""
    words = name.split()
    tails, cands, seen = [], [], set()
    for kind in ("rising", "top"):
        for q in related.get(kind, []):
            if q in seen or q == name:
                continue
            seen.add(q)
            if all(w in q.split() for w in words) or name in q:
                tails.append(q)
            elif len(q.split()) >= 2:
                cands.append({"phrase": q, "brand": False, "source": "searched", "rising": kind == "rising",
                              "evidence": f"searched on Google together with {name} ({kind})"})
    return tails, cands[:RELATED_KEPT]


def screen(model: str, name: str, ev: dict, cands: list[dict]) -> list[dict]:
    """The candidates with the model's view of each: `relevance`, `brand` (added to what
    the proposer said), `is_name`. A failed call returns them as they came, unscored: the
    screen narrows the table, it never empties it."""
    if not cands:
        return []
    posts = "\n".join(f"- ({p['likes']} likes) @{p['by']}: {p['text'][:POST_CHARS]}" for p in ev["posts"][:6])
    user = f"NAME: {name}\n\nEVIDENCE:\n{posts or ev['readme'][:1200]}\n\nCANDIDATES:\n" + json.dumps(
        [{"i": i, "keyword": c["phrase"]} for i, c in enumerate(cands)], ensure_ascii=False)
    try:
        answer = aisa.chat(model, SCREEN, user, max_tokens=600)
    except aisa.AisaError:
        return cands
    m = re.search(r"\[.*\]", answer, re.S)
    try:
        views = {int(x["i"]): x for x in json.loads(m.group(0))} if m else {}
    except (ValueError, KeyError, TypeError):
        return cands
    out = []
    for i, c in enumerate(cands):
        v = views.get(i)
        try:
            out.append(dict(c, relevance=float(v["score"]), brand=c["brand"] or bool(v.get("brand")), is_name=bool(v.get("name")))
                       if v else c)
        except (KeyError, TypeError, ValueError):
            out.append(c)
    return out


def other_names(name: str, viewed: list[dict]) -> list[dict]:
    """Names of other things that are rising in searches beside this one: leads of their
    own. A query sharing a word of the name is the same family ("google nano banana",
    "nano banana pro" beside "nano banana 2.1"), not another thing."""
    family = {w for w in name.split() if w.isalpha() and len(w) > 2}
    out = [{"term": u["phrase"], "with": name} for u in viewed
           if u.get("is_name") and u.get("rising") and not family & set(u["phrase"].split())]
    return out[:COSEARCH_KEPT]


def relevant(cands: list[dict]) -> list[dict]:
    """Candidates that pass the screen: not another thing's name, and related enough."""
    return [c for c in cands if not c.get("is_name") and c.get("relevance", 1.0) >= RELEVANT_MIN]


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


WORLD = {"unsettled": review.UNSETTLED_DAYS, "window": 30, "factor": review.RISE_FACTOR, "days": 2}
# One country, 30 days, settled to yesterday (goanyapi.daily_series). The rise is judged in
# the last 10 days against the 20 before. An established term has a high baseline, so the
# bar is 1.5x for three days: "photoshop alternative" ran 77-100 against 50 for five days
# after PhotoCraft appeared, a real move that 2x would miss.
COUNTRY = {"unsettled": 0, "window": 10, "factor": 1.5, "days": 3}


def shape(points: list[tuple[date, int]], today: date, rule: dict = WORLD) -> dict:
    """What a term's own Trends curve says: is it new, when did it start rising, where is
    the peak, what is it doing now. `points` is the daily series on its own 0-100 scale.
    Today's value covers part of a day and is dropped, with the days `rule` calls
    unsettled; "now" means the last days that are left. A rise is judged inside the last
    `window` days against the level before them, so an old peak does not count, and it
    needs `days` days above the line: a term with few searches shows single-day spikes
    out of nothing ("debloat macos": 0, 0, 100, 0, 0)."""
    cut = today - timedelta(days=rule["unsettled"])
    points = [(d, v) for d, v in points if d < cut]
    top = max((v for _, v in points), default=0)
    if not top:
        return {"no_data": True}
    # Back onto 0-100: when a dropped day held the series' 100, the real days sit squeezed
    # under 10 and no threshold in points would mean anything.
    points = [(d, round(v * 100 / top)) for d, v in points]
    end = points[-1][0]
    start = end - timedelta(days=rule["window"])
    old = [v for d, v in points if d < start]
    window = [(d, v) for d, v in points if d >= start]
    base = statistics.mean(old) if old else 0.0
    peak_day, peak = max(window, key=lambda p: (p[1], p[0]))
    line = max(base * rule["factor"], base + review.RISE_MIN)
    above = [d for d, v in window if v >= line]
    rose = len(above) >= rule["days"]
    week, before = [v for _, v in points[-RECENT_DAYS:]], [v for _, v in points[-2 * RECENT_DAYS:-RECENT_DAYS]]
    out = {"no_data": False, "base": round(base, 1), "peak": peak, "peak_day": peak_day.isoformat(),
           "rose": rose, "new": rose and base < NEW_BASE_MAX,
           # the last settled week against the week before it; None when that week held too
           # little to divide by ("ai audio detector" read x43 on a week of near-zeros)
           "momentum": round(statistics.mean(week) / statistics.mean(before), 1)
           if before and statistics.mean(before) >= MOMENTUM_MIN_BASE else None}
    if not rose:
        return {**out, "now": "flat"}
    # The rise that holds the peak: walk back from the peak while each day is above the
    # line. The first day above it anywhere in the window can be an earlier, unrelated blip.
    started, up = peak_day, set(above)
    while started - timedelta(days=1) in up:
        started -= timedelta(days=1)
    out["started"] = started.isoformat()
    latest = max(v for d, v in window if d > end - timedelta(days=NOW_DAYS))
    out["now"] = "rising" if (end - peak_day).days < NOW_DAYS else "holding" if latest >= HOLD_SHARE * peak else "fading"
    return out


def country_series(rows: list[dict], c: dict) -> tuple[dict[str, list], int, list[str]]:
    """The one-country series for the rows worth it: the names, then the generic terms
    with at least `country_min_volume` searches a month, `country_max` rows at most."""
    picked = [r for r in rows if r["kind"] == "name"] + \
        sorted((r for r in rows if r["kind"] == "generic" and r.get("volume", 0) >= c["country_min_volume"]), key=lambda r: -r["volume"])
    out, cost, errors = {}, 0, []
    for r in picked[:c["country_max"]]:
        try:
            out[r["phrase"]], spent = goanyapi.daily_series(r["phrase"], c["related_geo"])
            cost += spent
        except goanyapi.GoAnyError as exc:
            errors.append(f"{r['phrase']}: {exc}")
    return out, cost, errors


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
    window = pair[-WORLD["window"]:]
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


def measure(rows: list[dict], series: dict[str, dict], min_daily: int, today: date,
            country: dict[str, list] | None = None) -> float | None:
    """Fills each row with its shape, size and decision. Returns the benchmark's calibrated
    size. A row with a one-country series takes its shape from that (`trend_geo` says so)."""
    for r in rows:
        r["_pair"] = series.get(r["phrase"], {}).get("pair") or []
    daily = bench_daily(rows)
    for r in rows:
        solo = series.get(r["phrase"], {}).get("solo") or []
        local = (country or {}).get(r["phrase"])
        s = shape(local, today, COUNTRY) if local else shape(solo, today)
        if local and not s.get("no_data"):
            r["trend_geo"] = True
        elif local:
            s = shape(solo, today)
        z = size(r.pop("_pair"), today, daily)
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
    asked, c0 = 0, 0
    tails: dict[str, list[str]] = {}
    cosearch: list[dict] = []
    related_errors: list[str] = []
    use_related = bool(goanyapi.key()) and c.get("related", True)
    for name in todo:
        cands = [dict(u, source="model") for u in propose(c["model"], name, ev[name])]
        if use_related:
            try:
                related, cost_r = goanyapi.related_queries(name, c["related_geo"])
            except goanyapi.GoAnyError as exc:
                related, cost_r = {}, 0
                related_errors.append(f"{name}: {exc}")
            c0 += cost_r
            tails[name], searched = split_related(name, related)
            have = {u["phrase"] for u in cands}
            cands += [u for u in searched if u["phrase"] not in have]
        asked += len(cands)
        viewed = screen(c["model"], name, ev[name], cands)
        cosearch += other_names(name, viewed)
        for u in relevant(viewed):
            row = proposed.setdefault(u["phrase"], {**u, "term": u["phrase"], "kind": "generic", "names": []})
            row["names"].append(name)
            row["brand"] |= u["brand"]
            if u["source"] == "searched":
                row["source"] = "searched"
    bench = c["benchmark"].lower()
    vol, c2 = volumes(sorted(proposed), c["location_code"])
    generic = sorted((dict(r, **vol[p]) for p, r in proposed.items() if vol.get(p, {}).get("volume", 0) >= c["min_volume"]),
                     key=lambda r: -r["volume"])[:c["trends_max"]]
    rows = [{"term": n, "phrase": n, "kind": "name", "names": [], "brand": True, "evidence": "", **vol.get(n, {})} for n in todo] + generic
    series, c3 = fetch_series([r["phrase"] for r in rows], bench, today)
    local, c4, local_errors = country_series(rows, c) if goanyapi.key() and c.get("country_trends", True) else ({}, 0, [])
    daily = measure(rows, series, c["min_daily"], today, local)
    order = {"prioritize": 0, "watch": 1, "skip": 2}
    rows.sort(key=lambda r: (order[r["decision"]], -(r.get("per_day") or 0), -(r.get("volume") or 0)))
    for name in todo:
        s = seen.setdefault(name, {"first": today.isoformat(), "runs": 0})
        s["runs"] += 1
    cutoff = (today - timedelta(days=STATE_DAYS)).isoformat()
    path.write_bytes(gzip.compress(json.dumps({n: s for n, s in seen.items() if s["first"] >= cutoff}).encode()))
    return {"names": todo, "rows": rows, "proposed": asked, "relevant": len(proposed), "kept": len(generic), "benchmark": bench,
            "bench_daily": round(daily) if daily else None, "volume_month": next((r["month"] for r in generic if r.get("month")), ""),
            "no_evidence": [n for n in todo if not ev[n]["posts"] and not ev[n]["readme"]],
            "related": use_related, "tails": {n: v for n, v in tails.items() if v}, "cosearch": cosearch,
            "related_errors": related_errors, "geo": c["related_geo"], "country_errors": local_errors,
            "cost_micros": cost + c0 + c2 + c3 + c4}


READ_KINDS = {"x", "hf", "breakout", "newsite"}
READ_MIN = 0.8


def names_to_read(leads_today: list[dict], recent_sources: list[dict]) -> list[str]:
    """The leads worth reading for their generic terms: a thing someone released or built,
    not a word that surged. Terms that only the word-count signals found (new sitemap URLs,
    repos sharing a word) are words like "mcd" and "context protocol", or URL fragments
    like "kr.co.klisten.api": the first live run read five of those (2026-10-12). A lead
    needs a signal that reports things and a name score of READ_MIN; unscored leads pass."""
    out = []
    for r in [*leads_today, *recent_sources]:
        named = r.get("named")
        if READ_KINDS & set(r.get("kinds", [])) and (named is None or named >= READ_MIN) and r["term"] not in out:
            out.append(r["term"])
    return out


NOW_ZH = {"rising": "还在涨", "holding": "维持", "fading": "回落", "flat": "没动"}
DECISION_ZH = {"prioritize": "**优先**", "watch": "观察", "skip": "跳过"}


def _row(r: dict) -> str:
    generic, none = r["kind"] == "generic", r.get("no_data")
    peak = f"{r['peak_vs']} vs {r['bench_level']}" if "peak_vs" in r else "—"
    return (f"| **{r['phrase']}**{' 🔎' if r.get('source') == 'searched' else ''}{' ⚠' if generic and r['brand'] else ''} | "
            f"{'通用词' if generic else '名字'} | "
            f"{', '.join(r['names']) or '—'} | {'—' if none else '是' if r['new'] else '否'} | {r.get('per_day', '—')} | "
            f"{r.get('started') or '—'} | {peak} | {'—' if none else r['peak_day']} | "
            f"{'×' + str(r['momentum']) if r.get('momentum') is not None else '—'} | "
            f"{'还读不出' if none else NOW_ZH[r['now']]}{' (US)' if r.get('trend_geo') else ''} | {DECISION_ZH[r['decision']]} |")


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
    lines += [f"今天读了:{', '.join(uc['names'])}。提出 {uc['proposed']} 个通用写法,{uc['relevant']} 个通过相关性筛选,其中 {uc['kept']} 个月搜不低于 {c['min_volume']}"
              f"({uc['volume_month'] or '?'} 数据)。日搜是估算:通用词用它自己的月搜索量沿 Trends 曲线推到现在;{bench}。", "",
              f"| 关键词 | 类型 | 来自 | 新词? | 估算日搜 | 开始上涨 | 峰值 vs {uc['benchmark']} | 峰值日 | 近 7 天比前 7 天 | 现在 | 决策 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    lines += [_row(r) for r in uc["rows"]]
    lines += ["", f"决策规则:优先 = 近 30 天涨过、现在还在高位、估算日搜不低于 {c['min_daily']}。观察 = 涨了但规模小;还太早读不出;"
              "或者没动但本身就有这个规模的稳定需求。跳过 = 已回落,或没动且规模小。Trends 最后两天的数据还没结算,不计入。"]
    if any(r["kind"] == "generic" and r["brand"] for r in uc["rows"]):
        lines.append("⚠ = 这个词带着别人的品牌或产品名,法务和定位风险需要自己判断。")
    if any(r.get("trend_geo") for r in uc["rows"]):
        lines.append("(US) = 走势读自美国的 30 天日数据(GoAnyAPI),结算到昨天;在这份数据里,比之前高 50% 且持续三天算上涨。其余行用的是全球数据。")
    if uc.get("country_errors"):
        lines.append(f"国家数据获取失败,已退回全球数据:{'; '.join(uc['country_errors'])}。")
    if any(r.get("source") == "searched" for r in uc["rows"]):
        lines.append("🔎 = 来自 Google Trends 的相关查询:有人把它和这个名字一起搜(GoAnyAPI)。")
    said = [f"- **{r['phrase']}**({', '.join(r['names'])}):“{r['evidence'].replace('|', '/')}”"
            for r in uc["rows"] if r["kind"] == "generic" and r["evidence"] and r.get("source") != "searched"]
    if said:
        lines += ["", "原话(每个通用词的依据):", *said]
    if uc.get("tails"):
        lines += ["", "带着名字一起搜的写法(名字的长尾):", *[f"- **{n}**:{', '.join(v[:10])}" for n, v in uc["tails"].items()]]
    if uc.get("cosearch"):
        lines += ["", "一起被搜的其他名字(已记为线索):" + "、".join(f"{x['term']}(和 {x['with']} 一起)" for x in uc["cosearch"])]
    if uc.get("no_evidence"):
        lines += ["", f"没找到帖子或 README:{', '.join(uc['no_evidence'])}。"]
    if uc.get("related_errors"):
        lines += ["", f"相关查询失败:{'; '.join(uc['related_errors'])}。"]
    elif not uc.get("related"):
        lines += ["", "相关查询未开启:设置 GOANYAPI_API_KEY 后,会加入大家和每个名字一起搜的词。"]
    return lines


def leads(uc: dict) -> list[dict]:
    """The generic terms as rows for radar_leads, reviewed after 14 days like the names."""
    return [{"term": r["phrase"], "kinds": ["usecase"], "variants": [r["phrase"]],
             "signals": [f"{', '.join(r['names'])} 背后的通用词,月搜 {r.get('volume', 0)}"]}
            for r in uc.get("rows", []) if r["kind"] == "generic"] + \
        [{"term": x["term"], "kinds": ["cosearch"], "variants": [x["term"]], "signals": [f"在 Google 上和 {x['with']} 一起被搜"]}
         for x in uc.get("cosearch", [])]
