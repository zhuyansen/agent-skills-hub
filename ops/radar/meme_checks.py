"""Two checks for an AI video trend before it is worth a site: do people want to make
their own, and is the market still open. Used by memes.py.

intent()       the comments under the trend's most-liked TikTok videos (AIsa, $0.001 for
               50), and one model call that counts those wanting their own version:
               asking how it was made, which app, site or template, or for a link. Fans
               of a viral video mostly joke and praise (hotel lobby's two top videos on
               10-19: one comment in fifty asked how), so the share goes to Jev as
               evidence and in the mail, never as a bar of its own.
competition()  whether the obvious domains are still free (RDAP via rdap.org, free: 404
               means nobody holds it) and how many of Google's top 10 for the search
               term are already tool sites (DataForSEO through AIsa, $0.002). On 10-19
               "hotel lobby ai", a September trend, had six; a trend with none, and its
               domain free, is open. It also reads the first page of the trend's own name
               ($0.002 more) and keeps what holds the two pages besides tool sites:
               slots(), in shadow, shown nowhere until a review backs it.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import aisa

COMMENTS_TOOL = "get_tikhub_tiktok_app_v3_fetch_video_comments"
SERP_TOOL = "post_dataforseo_serp_google_organic_live_regular"
VIDEOS = 3
COMMENTS_PER_VIDEO = 50
COMMENT_CHARS = 120
MODEL = "claude-sonnet-4-6"
CROWDED = 4              # tool sites in Google's top 10: past the window (hotel lobby had 6 a month in)
TAKEN = 0.5              # platforms holding more than this share of the name's top 10 (slots())
# places that talk about a trend, not tools that make it
PLATFORMS = re.compile(r"(^|\.)(tiktok|youtube|instagram|facebook|x|twitter|reddit|pinterest|wikipedia|"
                       r"yahoo|msn|medium|quora|linkedin|threads|capcut|knowyourmeme|huggingface|github|"
                       r"apple|google|imdb|genius|spotify)\.[a-z.]+$")
TOOLISH = re.compile(r"\b(generator|maker|swap|create|try|free|online|upload|template|ai video|ai photo|app)\b", re.I)
UA = "agentskillshub-radar/1.0"
SYSTEM = (
    "You get the COMMENTS under popular TikTok videos of one internet trend, grouped by trend. For each trend, "
    "count the comments whose writer wants to make their own version: asking how it was made, which app, AI, site "
    "or template, asking for a link or a tutorial, or saying they want to try it. Jokes, praise, tags and reactions "
    "do not count. Answer with JSON only: {\"<trend>\": {\"wanting\": n, \"total\": m, \"quotes\": [up to 3 short "
    "quotes of wanting comments]}}."
)


def _aweme(url: str) -> str:
    m = re.search(r"/video/(\d+)", url or "")
    return m.group(1) if m else ""


def _comments(data: dict) -> list[str]:
    from memes import _find
    return [" ".join(str(c.get("text", "")).split())[:COMMENT_CHARS]
            for c in _find(data, lambda x: "text" in x and "digg_count" in x) if c.get("text")]


def intent(trends: list[dict]) -> tuple[dict[str, dict], int]:
    """{trend name: {"wanting", "total", "share", "quotes"}} for trends with TikTok posts."""
    videos = {}
    for t in trends:
        tiktok = sorted((p for p in t["posts"] if p["platform"] == "tiktok" and _aweme(p["url"])),
                        key=lambda p: -p["likes"])[:VIDEOS]
        if tiktok:
            videos[t["name"]] = [_aweme(p["url"]) for p in tiktok]
    if not videos:
        return {}, 0
    calls = [{"call_id": f"{name}|{i}", "tool": COMMENTS_TOOL, "arguments": {"aweme_id": aid, "count": COMMENTS_PER_VIDEO}}
             for name, ids in videos.items() for i, aid in enumerate(ids)]
    data, cost = aisa.call_all(calls)
    grouped: dict[str, list[str]] = {}
    for cid, d in data.items():
        grouped.setdefault(cid.split("|")[0], []).extend(_comments(d))
    grouped = {k: v for k, v in grouped.items() if v}
    if not grouped:
        return {}, cost
    user = "\n\n".join(f"TREND: {name}\n" + "\n".join(f"- {c}" for c in cs) for name, cs in grouped.items())
    answer = aisa.chat(MODEL, SYSTEM, user, max_tokens=1500)
    m = re.search(r"\{.*\}", answer, re.S)
    try:
        counted = json.loads(m.group(0)) if m else {}
    except ValueError:
        counted = {}
    out = {}
    for name, cs in grouped.items():
        c = counted.get(name) or {}
        total = int(c.get("total") or len(cs)) or len(cs)
        wanting = min(int(c.get("wanting") or 0), total)
        out[name] = {"wanting": wanting, "total": total, "share": round(wanting / total, 3),
                     "quotes": [str(q)[:COMMENT_CHARS] for q in (c.get("quotes") or [])[:3]]}
    return out, cost


def domains(name: str) -> list[str]:
    """'bulin 47 dance' -> bulin47danceai.com, bulin47dance-ai.com, bulin47dance.ai, bulin47danceai.app."""
    base = re.sub(r"[^a-z0-9]", "", name.lower().replace(" ai", ""))
    return [f"{base}ai.com", f"{base}-ai.com", f"{base}.ai", f"{base}ai.app"] if base else []


def rdap(domain: str) -> dict:
    """{"domain", "free": bool | None, "registered": date or ""}; None when RDAP did not say."""
    req = urllib.request.Request(f"https://rdap.org/domain/{domain}", headers={"User-Agent": UA,
                                                                              "Accept": "application/rdap+json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            data = json.load(res)
    except urllib.error.HTTPError as exc:
        return {"domain": domain, "free": True if exc.code == 404 else None, "registered": ""}
    except (OSError, ValueError):
        return {"domain": domain, "free": None, "registered": ""}
    when = next((e.get("eventDate", "")[:10] for e in data.get("events", []) if e.get("eventAction") == "registration"), "")
    return {"domain": domain, "free": False, "registered": when}


def serp(query: str) -> tuple[dict, int]:
    """Google's first page for `query`, US English: `top`, its ten organic results, and `blocks`,
    the other kinds of result on the page (ai_overview, video, short_videos, paid...). The regular
    endpoint names every kind on the page in item_types, at no extra cost (the 10-11 scenario
    check: an AI overview on 13 of 14 pages)."""
    data, cost = aisa.call([{"call_id": "s", "tool": SERP_TOOL, "arguments": {"body": [{
        "keyword": query, "location_code": 2840, "language_code": "en", "depth": 10}]}}])
    try:
        result = data["s"]["tasks"][0]["result"][0] or {}
    except (KeyError, IndexError, TypeError):
        result = {}
    top = [{"domain": (i.get("domain") or "").removeprefix("www."), "title": i.get("title") or ""}
           for i in result.get("items") or [] if i.get("type") == "organic"][:10]
    return {"top": top, "blocks": sorted(set(result.get("item_types") or []) - {"organic"})}, cost


def is_tool(item: dict, name: str) -> bool:
    base = re.sub(r"[^a-z0-9]", "", name.lower())
    if PLATFORMS.search(item["domain"]):
        return False
    return bool(TOOLISH.search(item["title"])) or (len(base) > 4 and base in item["domain"].replace("-", ""))


def page_slots(page: dict, name: str) -> dict:
    """What holds a first page: how many results are platforms (PLATFORMS) or tool sites, and the
    other blocks on it."""
    top = page["top"]
    return {"results": len(top), "platforms": sum(1 for i in top if PLATFORMS.search(i["domain"])),
            "tools": sum(1 for i in top if is_tool(i, name)), "blocks": page["blocks"]}


def slots(name: str, head: dict, tool: dict) -> dict:
    """The results pages' own slots, kept in shadow (radar_leads.evidence, meme.slots), shown
    nowhere. `head` is the page for the trend's name, `tool` the one for its search term ("<name>
    ai"). `taken`: platforms hold more than half of the name's top 10 and no ads show on the term's
    page, so searchers want the trend itself and nobody pays for a tool's click. Proposed on 10-31
    from a song meme whose name's page was held by video platforms, a short-video block and an AI
    overview: a tool site built for it got no impression on the name. A review against the radar's
    14-day verdicts decides whether it may ever hold a pick."""
    h, t = page_slots(head, name), page_slots(tool, name)
    t["ads"] = "paid" in t["blocks"]
    return {"head": h, "tool": t, "taken": h["results"] > 0 and h["platforms"] > h["results"] * TAKEN and not t["ads"]}


def competition(trend: dict) -> tuple[dict, int]:
    with ThreadPoolExecutor(4) as pool:
        doms = list(pool.map(rdap, domains(trend["name"])))
    page, cost = serp(trend["query"])
    try:   # the name's own page, for slots() only: when it fails, the check keeps its tool count
        head, more = serp(trend["name"]) if trend["name"] != trend["query"] else (page, 0)
    except Exception:  # noqa: BLE001
        head, more = None, 0
    return {"domains": doms, "free": [d["domain"] for d in doms if d["free"]], "results": len(page["top"]),
            "tools": [i["domain"] for i in page["top"] if is_tool(i, trend["name"])],
            "slots": slots(trend["name"], head, page) if head else None}, cost + more


def summary(trend: dict) -> str:
    """One line for the mail: '评论 8% 想自己做｜bulin47ai.com 还空着｜Google 前 10 有 2 个工具站'."""
    parts = []
    it = trend.get("intent")
    if it:
        parts.append(f"评论 {it['share']:.0%} 想自己做({it['wanting']}/{it['total']})")
    co = trend.get("competition")
    if co:
        taken = [d for d in co["domains"] if d["free"] is False]
        if co["free"]:
            parts.append(f"{co['free'][0]} 还空着")
        elif taken:
            parts.append(f"域名都被注册了(最早 {min(d['registered'] or '?' for d in taken)})")
        n = len(co["tools"])
        parts.append((f"Google 前 10 有 {n} 个工具站" + ("(已经挤了)" if n >= CROWDED else "")) if co["results"]
                     else "Google 还没有结果")
    return "｜".join(parts)
