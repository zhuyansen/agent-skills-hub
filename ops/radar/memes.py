"""Radar signal ①c: AI video trends people want to make their own version of.

Bulin 47's freestyle took off on TikTok in early October 2026 and people put themselves
into it with AI. One person saw it on 10-09 by searching TikTok for trends like the ones
the group was already building for (hotel lobby, ai raindance), bought a domain that
afternoon, and took $5,480 in the 72 hours after the first order; 85% of the money came
in those three days (luko/research/26-新词案例-Bulin47TikTok梗站.md). The other radar
signals watch model and product names and never saw it.

Each day this step:
  1. reads posts of the last WINDOW_DAYS days that talk about AI trends, on TikTok,
     Instagram Reels, YouTube Shorts and X (AIsa; QUERIES), and TikTok Creative Center's
     trending hashtags for the US (a tag new since yesterday, or one still near its peak,
     is shown to the model too). On 10-19 that list held #bulin47 and #burningbridgesai;
  2. asks a model which trends the posts show: a named video format that people recreate
     with AI, and the words they would search for a tool ("bulin 47 ai"). Trends the radar
     found before are given as examples (SEEDS);
  3. asks Jev whether a one-purpose site or app for it could sell now (OPPORTUNITY);
  4. trends at OPPORTUNITY_MIN or above become leads of kind "meme", their search term
     goes through the keyword table (Trends shape and size) and the 14-day review.

About $0.02 a day for the searches, plus the model and Jev. A trend lives about four
days, so a daily read already costs one of them; the 8-hourly source run is the next step.
"""
from __future__ import annotations

import gzip
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import aisa

WINDOW_DAYS = 7
STATE = "memes.json.gz"
SEEDS_DAYS = 21
SEEDS_MAX = 8
OPPORTUNITY_MIN = 0.55   # hotel lobby read 0.70 on 09-22, Bulin 47 0.65 on 10-10; on 10-19 ten of twelve trends were 0.50-0.56
MAX_MEMES = 12
POST_CHARS = 160
POSTS_PER_SOURCE = 25
TAGS = 100
MODEL = "claude-sonnet-4-6"
# what the trend posts say about themselves; checked on 10-19, each returned live trends
QUERIES = {
    "tiktok": ["ai trend", "ai edit trend", "how to make the ai trend", "ai template trend", "ai filter trend"],
    "instagram": ["ai trend", "viral ai edit"],
    "youtube": ["ai trend", "how to make ai trend"],
    "x": ['("ai trend" OR "viral ai" OR "ai template") (video OR edit OR filter) min_faves:300 -filter:replies'],
}
TOOLS = {"tiktok": "get_tikhub_tiktok_app_v3_fetch_video_search_result",
         "instagram": "get_tikhub_instagram_v2_search_reels",
         "youtube": "get_tikhub_youtube_web_v2_get_shorts_search",
         "x": "get_twitter_tweet_advanced_search",
         "tags": "post_tikhub_tiktok_ads_get_trends_hashtag_list"}
PLATFORM_ZH = {"tiktok": "TikTok", "instagram": "Ins", "youtube": "YouTube", "x": "X", "tags": "TikTok 话题榜"}
SYSTEM = (
    "You help someone who builds one-purpose AI tool sites for internet trends. You get recent POSTS from TikTok, "
    "Instagram, YouTube Shorts and X about AI trends, and TikTok's trending HASHTAGS. Find the TRENDS: a specific, "
    "named video or image format that ordinary people are recreating with AI, usually by putting themselves, a pet "
    "or a celebrity into it ('hotel lobby' Migos rap, Bulin 47 freestyle, 'AI arrest edit', 'AI slap', 'burning "
    "bridges'). Not a generic topic ('ai art', 'ai video'), not an AI tool or model by itself, not news, sport or a "
    "dance needing no AI.\n"
    "For each trend give: `name` (2-4 words, lowercase, as people say it), `query` (what someone would type into "
    "Google to make their own: usually '<name> ai' or '<name> ai generator'), `what` (one sentence: what people make), "
    "`posts` (the numbers of the posts and hashtags that show it). The query never holds 'capcut', 'template', "
    "'tutorial' or 'trend': those are how the posts talk, not what a buyer types. Merge spellings of the same trend. At most 12, "
    "most posted first. Answer with JSON only: {\"trends\": [...]}. No trend: {\"trends\": []}."
)
OPPORTUNITY = {"build_now": {"type": "noul", "instructions": {
    "question": "Could a one-purpose website or app that lets anyone make their own version of this trend (upload a "
                "photo, get the video or image) win paying users this week?",
    "focus": "`posts` are what was posted about it in the last week, with likes or views. Yes needs a visual format "
             "people want to be in or put someone into, whose recreations are themselves being posted, that AI "
             "makes in one step, and that is still rising (hotel lobby in September and Bulin 47 in October 2026 "
             "sold $5k-7k in their first week, both while CapCut templates for them existed). No for a trend past its "
             "peak, a plain filter or style every photo app already has, or one nobody would pay for."}}}
APP_OPPORTUNITY = {"build_now": {"type": "noul", "instructions": {
    "question": "Could a small team build a site or app for the need this new app proved and win paying users "
                "within a month?",
    "focus": "`app` is a new app climbing the App Store charts; `copies` are other apps released in the last 30 "
             "days on its search words. Yes when the need is plain, the app is simple to rebuild and the words are "
             "not crowded yet; no for a game, a brand's own app, a service tied to one place, or a crowded need."}}}


def _find(o, key):
    """The longest list of dicts in a response whose first item passes key()."""
    best = []
    stack = [o]
    while stack:
        x = stack.pop()
        if isinstance(x, list):
            if x and isinstance(x[0], dict) and key(x[0]) and len(x) > len(best):
                best = x
            stack += x
        elif isinstance(x, dict):
            stack += x.values()
    return best


def _clean(text: str) -> str:
    return " ".join(re.sub(r"#\w+", lambda m: m.group(0) if len(m.group(0)) < 25 else "", text or "").split())[:POST_CHARS]


def tiktok(data: dict, since: int) -> list[dict]:
    out = []
    for it in _find(data, lambda x: "aweme_info" in x or ("desc" in x and "statistics" in x)):
        a = it.get("aweme_info", it)
        if int(a.get("create_time") or 0) < since:
            continue
        s = a.get("statistics") or {}
        out.append({"text": _clean(a.get("desc", "")), "likes": int(s.get("digg_count") or 0), "views": int(s.get("play_count") or 0),
                    "day": date.fromtimestamp(a["create_time"]).isoformat(),
                    "url": f"https://www.tiktok.com/@{(a.get('author') or {}).get('unique_id', '')}/video/{a.get('aweme_id', '')}"})
    return out


def instagram(data: dict, since: int) -> list[dict]:
    out = []
    for it in _find(data, lambda x: any(k in x for k in ("taken_at", "like_count", "play_count")) or "media" in x):
        m = it.get("media", it)
        if int(m.get("taken_at") or 0) < since:
            continue
        cap = m.get("caption")
        cap = cap.get("text") if isinstance(cap, dict) else cap
        out.append({"text": _clean(cap or ""), "likes": int(m.get("like_count") or 0), "views": int(m.get("play_count") or 0),
                    "day": date.fromtimestamp(m["taken_at"]).isoformat(), "url": f"https://www.instagram.com/reel/{m.get('code', '')}/"})
    return out


_VIEWS = {"thousand": 1e3, "million": 1e6, "billion": 1e9}


def youtube(data: dict, since: int) -> list[dict]:
    """Shorts come back as YouTube's own page data: the title and views are in the
    accessibility text ('<title>, 2.8 million views - play Short'), with no date: the
    upload-time filter returned nothing on 10-19, so these may be older than a week."""
    out, seen = [], set()
    for m in re.finditer(r'"accessibilityText": "(.{5,200}?), ([\d.,]+)( thousand| million| billion)? views? - play Short"',
                         json.dumps(data, ensure_ascii=False)):
        title, n, unit = m.group(1), float(m.group(2).replace(",", "")), (m.group(3) or "").strip()
        if title in seen:
            continue
        seen.add(title)
        out.append({"text": _clean(title), "likes": 0, "views": int(n * _VIEWS.get(unit, 1)), "day": "", "url": ""})
    return out


def x(data: dict, since: int) -> list[dict]:
    out = []
    for t in data.get("tweets") or []:
        try:
            day = datetime.strptime(t["createdAt"], "%a %b %d %H:%M:%S %z %Y")
        except (KeyError, ValueError):
            continue
        if day.timestamp() < since:
            continue
        out.append({"text": _clean(t.get("text", "")), "likes": int(t.get("likeCount") or 0), "views": int(t.get("viewCount") or 0),
                    "day": day.date().isoformat(), "url": t.get("url") or t.get("twitterUrl") or ""})
    return out


READERS = {"tiktok": tiktok, "instagram": instagram, "youtube": youtube, "x": x}


def calls(today: date) -> list[dict]:
    since = (today - timedelta(days=WINDOW_DAYS)).isoformat()
    out = []
    for platform, queries in QUERIES.items():
        for i, q in enumerate(queries):
            args = {"tiktok": {"keyword": q, "publish_time": WINDOW_DAYS, "sort_type": 1, "count": 30},
                    "instagram": {"keyword": q},
                    "youtube": {"search_query": q},   # with upload_time the tool returned nothing (10-19)
                    "x": {"query": f"{q} since:{since}", "queryType": "Top"}}[platform]
            out.append({"call_id": f"{platform}:{i}", "tool": TOOLS[platform], "arguments": args})
    out.append({"call_id": "tags", "tool": TOOLS["tags"], "arguments": {"body": {"country_code": "US", "period": 7, "limit": TAGS}}})
    return out


def hashtags(data: dict, before: dict[str, int]) -> list[dict]:
    """Trending tags worth showing the model: new on the list since yesterday, or still
    near the top of their own curve (a tag whose curve has fallen to nothing is over)."""
    out = []
    for t in _find(data, lambda x: "hashtagName" in x):
        curve = [float(p.get("value") or 0) for p in t.get("popularityCurve") or []]
        new = bool(before) and t["hashtagName"] not in before
        if new or (curve and curve[-1] >= 0.6 * max(curve) and min(curve[:2] or [0]) < 20):
            out.append({"tag": t["hashtagName"], "rank": t.get("rankIndex"), "videos": t.get("publishCnt"),
                        "views": t.get("vv"), "curve": [round(v) for v in curve], "new": new})
    return out


def _all_tags(data: dict) -> dict[str, int]:
    return {t["hashtagName"]: t.get("rankIndex") for t in _find(data, lambda x: "hashtagName" in x)}


def extract(posts: list[dict], tags: list[dict], seeds: list[str]) -> list[dict]:
    lines = [f"[{i}] {PLATFORM_ZH[p['platform']]} {p['day'] or 'this week'} ♥{p['likes']} ▶{p['views']}: {p['text']}"
             for i, p in enumerate(posts)]
    lines += [f"[t{i}] #{t['tag']} rank {t['rank']}, {t['videos']} videos, curve {t['curve']}" for i, t in enumerate(tags)]
    user = ("Trends found on earlier days, for the kind of thing to look for (report them again only if these posts "
            f"show them): {', '.join(seeds) or 'none yet'}\n\nPOSTS AND HASHTAGS:\n" + "\n".join(lines))
    answer = aisa.chat(MODEL, SYSTEM, user, max_tokens=2000)
    m = re.search(r"\{.*\}", answer, re.S)
    trends = json.loads(m.group(0)).get("trends", []) if m else []
    out = []
    for t in trends[:MAX_MEMES]:
        name = " ".join(str(t.get("name", "")).lower().split())
        if not name:
            continue
        refs = [str(r).strip("[]") for r in t.get("posts") or []]
        ev = [posts[int(r)] for r in refs if r.isdigit() and int(r) < len(posts)]
        tg = [tags[int(r[1:])] for r in refs if r.startswith("t") and r[1:].isdigit() and int(r[1:]) < len(tags)]
        out.append({"name": name, "query": " ".join(str(t.get("query") or f"{name} ai").lower().split()),
                    "what": str(t.get("what", ""))[:160], "posts": ev, "tags": tg})
    return out


def jev():
    try:
        from jev_client import OpenRouter
        return OpenRouter()
    except Exception:  # noqa: BLE001 — no key: the trends go out without the score
        return None


def opportunity(client, state: dict, questions: dict = OPPORTUNITY) -> float | None:
    if client is None:
        return None
    try:
        return float(client.decisions(json.dumps(state, ensure_ascii=False), questions).answers["build_now"].get("noul", 0.0))
    except Exception:  # noqa: BLE001 — no credit or a timeout
        return None


def load(snaps: Path) -> dict:
    path = snaps / STATE
    return json.loads(gzip.decompress(path.read_bytes())) if path.exists() else {}


def memes(snaps: Path, today: date | None = None) -> dict:
    today = today or date.today()
    state = load(snaps)
    since = int(datetime.combine(today - timedelta(days=WINDOW_DAYS), datetime.min.time(), timezone.utc).timestamp())
    data, cost = aisa.call_all(calls(today))
    posts, errors = [], []
    for c in calls(today):
        platform = c["call_id"].split(":")[0]
        if platform == "tags":
            continue
        if c["call_id"] not in data:
            errors.append(f"{PLATFORM_ZH[platform]} “{c['arguments'].get('keyword') or c['arguments'].get('search_query') or 'x'}”")
            continue
        got = sorted(READERS[platform](data[c["call_id"]], since), key=lambda p: -(p["likes"] or p["views"] / 50))
        posts += [{**p, "platform": platform} for p in got[:POSTS_PER_SOURCE]]
    # one post found by two queries is one post
    posts = list({(p["platform"], p["text"]): p for p in posts}.values())
    before = state.get("tags", {}) if state.get("date") != today.isoformat() else state.get("tags_before", {})
    all_tags = _all_tags(data.get("tags") or {})
    if "tags" not in data:
        errors.append("TikTok 话题榜")
    tags = hashtags(data.get("tags") or {}, before)

    known = {n: m for n, m in state.get("memes", {}).items() if m["last"] >= (today - timedelta(days=SEEDS_DAYS)).isoformat()}
    seeds = [n for n, m in sorted(known.items(), key=lambda kv: kv[1]["last"], reverse=True)
             if (m.get("score") or 0) >= OPPORTUNITY_MIN][:SEEDS_MAX]
    found = extract(posts, tags, seeds) if posts or tags else []

    client, terms = jev(), []
    for m in found:
        m["score"] = opportunity(client, {"trend": m["name"], "what": m["what"], "today": today.isoformat(),
                                          "posts": [f"{PLATFORM_ZH[p['platform']]} {p['day']} ♥{p['likes']} ▶{p['views']}: {p['text']}"
                                                    for p in m["posts"][:6]],
                                          "tiktok_hashtags": [f"#{t['tag']} curve {t['curve']}" for t in m["tags"]]})
        m["platforms"] = sorted({p["platform"] for p in m["posts"]} | ({"tags"} if m["tags"] else set()))
        prev = known.get(m["name"])
        m["first"] = prev["first"] if prev else today.isoformat()
        m["new"] = prev is None
        known[m["name"]] = {"first": m["first"], "last": today.isoformat(), "score": m["score"], "query": m["query"]}
        if m["new"] and (m["score"] is None or m["score"] >= OPPORTUNITY_MIN):
            top = max(m["posts"], key=lambda p: p["likes"] or p["views"] / 50, default=None)
            terms.append({"term": m["query"], "recent": len(m["posts"]),
                          "note": f"①梗 {'/'.join(PLATFORM_ZH[p] for p in m['platforms'])} {len(m['posts'])} 帖"
                                  + (f",Jev 机会 {m['score']:.2f}" if m["score"] is not None else ""),
                          "examples": [m["what"], *(p["text"] for p in m["posts"][:2])], "variants": [m["query"], m["name"]],
                          "posts": [{"account": PLATFORM_ZH[p["platform"]], "likes": p["likes"], "url": p["url"], "text": p["text"]}
                                    for p in ([top] if top else [])]})
    found.sort(key=lambda m: -(m["score"] if m["score"] is not None else 0.5))
    snaps.mkdir(parents=True, exist_ok=True)
    (snaps / STATE).write_bytes(gzip.compress(json.dumps({
        "date": today.isoformat(), "tags": all_tags or before, "tags_before": before, "memes": known}, ensure_ascii=False).encode()))
    return {"today": today.isoformat(), "posts": len(posts), "by_platform": {k: sum(p["platform"] == k for p in posts) for k in QUERIES},
            "tags": len(tags), "first_run": not before, "memes": found, "terms": terms, "seeds": seeds,
            "errors": errors, "jev": client is not None, "cost_micros": cost}


def _n(v: int) -> str:
    return f"{v / 1e6:.1f}M" if v >= 1e6 else f"{v / 1e3:.0f}k" if v >= 1e3 else str(v)


def section(b: dict) -> list[str]:
    if b.get("skipped"):
        return []
    lines = ["", f"### ① AI 视频梗(TikTok / Ins / YouTube / X 近 {WINDOW_DAYS} 天 + TikTok 话题榜;"
             f"Jev 机会分 ≥{OPPORTUNITY_MIN} 的进候选词;🆕 = 第一次出现)", ""]
    if b.get("error"):
        return lines + [f"失败:{b['error']}"]
    found = b.get("memes") or []
    if not found:
        return lines + [f"今天没认出梗({b['posts']} 条帖子,{b['tags']} 个话题)"]
    lines += ["| 梗 | 搜索词 | 做什么 | 出现在 | 最热一条 | TikTok 话题曲线 | Jev 机会 | 首次 |", "|---|---|---|---|---|---|---|---|"]
    for m in found:
        top = max(m["posts"], key=lambda p: p["likes"] or p["views"] / 50, default=None)
        hot = (f"[♥{_n(top['likes'])} ▶{_n(top['views'])}]({top['url']})" if top and top["url"] else
               f"▶{_n(top['views'])}" if top else "—")
        curve = "<br>".join(f"#{t['tag']} {'→'.join(str(v) for v in t['curve'][-5:])}" for t in m["tags"][:2]) or "—"
        where = "、".join(f"{PLATFORM_ZH[p]}{sum(q['platform'] == p for q in m['posts']) or ''}" for p in m["platforms"])
        score = f"**{m['score']:.2f}**" if m["score"] is not None and m["score"] >= OPPORTUNITY_MIN else \
            f"{m['score']:.2f}" if m["score"] is not None else "—"
        lines.append(f"| {'🆕 ' if m['new'] else ''}**{m['name']}** | {m['query']} | {m['what'].replace('|', '/')} | {where} | "
                     f"{hot} | {curve} | {score} | {m['first'][5:]} |")
    lines += ["", "Jev 机会 = Jev 判断“现在做一个单功能站或应用让人做自己的版本，这周能不能卖出去”。"
              "梗大约 4 天见顶，85% 的钱在头 72 小时(Bulin 47 的复盘),看到就要当天动手。"]
    return lines


def status(b: dict) -> str:
    if b.get("skipped"):
        return "- ① 梗:跳过"
    if b.get("error"):
        return f"- ① 梗:{b['error']}"
    s = (f"- ① 梗:{b['posts']} 条帖子(" + "、".join(f"{PLATFORM_ZH[k]} {v}" for k, v in b["by_platform"].items())
         + f"),{b['tags']} 个上升话题,认出 {len(b['memes'])} 个梗")
    if b.get("first_run"):
        s += ",首次运行,话题榜没有昨天的名单"
    if not b.get("jev"):
        s += ",没有 Jev 打分"
    if b.get("errors"):
        s += ";没取到:" + "、".join(b["errors"])
    return s


if __name__ == "__main__":
    # python ops/radar/memes.py <snapshot-dir>: the section alone, for a dry run
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "jev-review"))
    res = memes(Path(sys.argv[1]))
    print("\n".join(section(res)))
    print(status(res), f"${res['cost_micros'] / 1e6:.3f}")
