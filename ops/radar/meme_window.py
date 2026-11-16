"""做站体检 for a new AI video trend: is the window for a one-purpose site open today?

The radar dates a trend from the oldest post it read this week, which says when the
radar saw it, not where the trend is. On 2026-11-03 three of four leads it mailed had
how-to and template posts out in numbers for 10 to 33 days already (Tiny Desk, dime dime
baby, the zombie templates). Those posts are when people start wanting their own: on
the 2026-11-02 family trees they came 4 to 6 days after the first AI versions, and the
Bulin 47 site that took $5,480 opened two days after they started (luko/research/26).

For a trend's search term this searches TikTok (three queries, most liked and most
related), X and Instagram for the last LOOKBACK_DAYS, reads the details of the TikTok
sounds the trend's posts share most, and keeps only posts whose caption names the trend
(a short name brings back other memes: "fan lift" found September's ceiling-fan outfit
posts). The verdict, from the first day how-to or template posts came three within three
days:
  还早        AI versions, no how-to wave yet           mailed
  窗口正开    the wave began at most OPEN_DAYS ago      mailed
  窗口在关    at most CLOSING_DAYS ago                  held (radar._meme_held)
  多半晚了    longer ago                                held
  看不出来    no AI version among the posts             held
Ported from ~/content/memetree/check.py, where the same check runs by hand.

About $0.02 a trend (AIsa, no model). The answer for a term is kept CACHE_HOURS in the
source snapshot (STATE), with its sounds' counts, so a later check gives their real rate.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import aisa

STATE = "meme_window.json"
LOOKBACK_DAYS = 45
CACHE_HOURS = 12
OPEN_DAYS = 3
CLOSING_DAYS = 10
AI_VIEWS_MIN = 10_000
HOW_TO_VIEWS_MIN = 1_000
FEW = 15                 # fewer captions naming the trend than this: the verdict may be another meme's
SOUNDS = 3
LABEL = "做站体检:"      # starts the check's part of a lead's checks and note (radar._meme_held reads it)
MAILED = ("还早", "窗口正开")
TOOLS = {"tiktok": "get_tikhub_tiktok_app_v3_fetch_video_search_result",
         "x": "get_twitter_tweet_advanced_search",
         "instagram": "get_tikhub_instagram_v2_search_reels",
         "sound": "get_tikhub_tiktok_app_v3_fetch_music_detail"}
AI_TOOLS = {"dreamina": "Dreamina", "kling": "Kling", "higgsfield": "Higgsfield", "seedance": "Seedance", "hailuo": "Hailuo",
            "pixverse": "PixVerse", "vidu": "Vidu", "runway": "Runway", "veo": "Veo", "sora": "Sora", "pika": "Pika",
            "hedra": "Hedra", "viggle": "Viggle", "midjourney": "Midjourney", "nano banana": "Nano Banana",
            "grok imagine": "Grok Imagine", "capcut": "CapCut"}
AI_WORD = re.compile(r"(?<!\w)(ai|ia|ki|ии)(?!\w)", re.I)
HOW_TO = re.compile(r"how to (make|do|create|get)|tutorial|tutori[ae]l|c[oó]mo hacer|como fazer|cara (membuat|bikin)|"
                    r"как сделать|come fare|comment faire|template|plantilla|plantilha|templat|capcutpioneer|prompt|教程|怎么做|模板", re.I)
LANGS = {"en": "英语", "es": "西语", "pt": "葡语", "id": "印尼语", "in": "印尼语", "ms": "马来语", "ru": "俄语", "it": "意大利语",
         "fr": "法语", "de": "德语", "ja": "日语", "ko": "韩语", "ar": "阿拉伯语", "tr": "土耳其语", "vi": "越南语", "th": "泰语",
         "zh": "中文", "hi": "印地语", "tl": "菲律宾语", "fil": "菲律宾语", "pl": "波兰语", "nl": "荷兰语"}
STOP = set("the a an and or of to in on at for with is are it its this that my your me i you we they "
           "de la el en y que los las un una por con para se lo al del mi tu su es o".split())
END_STOP = {"how", "to", "make", "do", "your", "own"}


def _find(o, key):
    """The longest list of dicts in a response whose first item passes key() (as memes._find)."""
    best, stack = [], [o]
    while stack:
        x = stack.pop()
        if isinstance(x, list):
            if x and isinstance(x[0], dict) and key(x[0]) and len(x) > len(best):
                best = x
            stack += x
        elif isinstance(x, dict):
            stack += x.values()
    return best


def _iso(ts) -> str:
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%d") if ts else ""


GENERIC = {"video", "videos", "trend", "edit", "filter", "effect", "template"}


def base_name(term: str) -> str:
    """The trend's own words: 'outstanding tiny desk ai' → 'outstanding tiny desk', 'zombie
    apocalypse ai video' → 'zombie apocalypse'. The queries add 'ai' themselves; a trailing
    generic word goes while three or more words are left ('ai dunking video' keeps 'video')."""
    words = [w for w in term.split() if w.lower() not in ("ai", "ia")]
    while len(words) > 2 and words[-1].lower() in GENERIC:
        words.pop()
    return " ".join(words) or term


def calls(term: str, today: date) -> list[dict]:
    base, since = base_name(term), (today - timedelta(days=LOOKBACK_DAYS)).isoformat()
    out = []
    for i, kw in enumerate([base, f"{base} ai", f"how to make {base} ai"]):
        for sort in (1, 0):   # most liked, then most related
            out.append({"call_id": f"tiktok:{i}:{sort}", "tool": TOOLS["tiktok"],
                        "arguments": {"keyword": kw, "publish_time": 90, "sort_type": sort, "count": 30}})
    for qt in ("Top", "Latest"):
        out.append({"call_id": f"x:{qt}", "tool": TOOLS["x"],
                    "arguments": {"query": f'"{base}" since:{since} -filter:replies', "queryType": qt}})
    out.append({"call_id": "instagram:0", "tool": TOOLS["instagram"], "arguments": {"keyword": base}})
    return out


def read(cid: str, data: dict) -> list[dict]:
    """The posts in one answer as {id, platform, day, text, lang, views, ai, tools, sound}."""
    out, kind = [], cid.split(":")[0]
    if kind == "tiktok":
        for it in _find(data, lambda x: "aweme_info" in x or ("aweme_id" in x and "statistics" in x)):
            a = it.get("aweme_info", it)
            if not a.get("aweme_id"):
                continue
            m, tpl = a.get("music") or {}, (a.get("cc_template_info") or {}).get("template_id")
            out.append({"id": f"tt:{a['aweme_id']}", "platform": "tiktok", "day": _iso(a.get("create_time")),
                        "text": " ".join(str(a.get("desc") or "").split())[:280], "lang": a.get("desc_language") or "",
                        "views": int((a.get("statistics") or {}).get("play_count") or 0),
                        "ai": bool((a.get("aigc_info") or {}).get("created_by_ai")),
                        "tools": [x["keyword"] for x in a.get("anchors") or [] if x.get("keyword")] + (["CapCut template"] if tpl else []),
                        "sound": {"id": str(m.get("id_str") or m.get("id") or ""), "title": m.get("title") or "",
                                  "owner": (m.get("owner_handle") or "").lower()} if m else None})
    elif kind == "x":
        for t in data.get("tweets") or []:
            try:
                day = datetime.strptime(t["createdAt"], "%a %b %d %H:%M:%S %z %Y").astimezone(timezone.utc).strftime("%Y-%m-%d")
            except (KeyError, ValueError):
                continue
            out.append({"id": f"x:{t.get('id')}", "platform": "x", "day": day, "text": " ".join(str(t.get("text") or "").split())[:280],
                        "lang": t.get("lang") or "", "views": int(t.get("viewCount") or 0), "ai": False, "tools": [], "sound": None})
    elif kind == "instagram":
        for it in _find(data, lambda x: "taken_at" in x or "media" in x):
            m = it.get("media", it)
            if not m.get("code"):
                continue
            cap = m.get("caption")
            out.append({"id": f"ig:{m['code']}", "platform": "instagram", "day": _iso(m.get("taken_at")),
                        "text": " ".join(str((cap.get("text") if isinstance(cap, dict) else cap) or "").split())[:280],
                        "lang": "", "views": int(m.get("play_count") or m.get("ig_play_count") or 0), "ai": False, "tools": [], "sound": None})
    return out


def names_it(term: str):
    """A caption names the trend when it has two thirds of its words (ai left out), or all of
    them written as one word (#bulin47)."""
    toks = [t for t in re.findall(r"[^\W_]+", base_name(term).lower()) if t not in ("ai", "ia")]
    need, joined = -(-2 * len(toks) // 3), "".join(toks)

    def test(p: dict) -> bool:
        text = unicodedata.normalize("NFKC", p["text"]).lower()
        return bool(toks) and (len(set(toks) & set(re.findall(r"[^\W_]+", text))) >= need or joined in re.sub(r"[\W_]+", "", text))
    return test


def tools_of(p: dict) -> set[str]:
    text = (p["text"] + " " + " ".join(p["tools"])).lower()
    return {label for key, label in AI_TOOLS.items() if key in text}


def is_ai(p: dict) -> bool:
    return p["ai"] or bool(AI_WORD.search(p["text"])) or bool(tools_of(p) - {"CapCut"})


def is_how_to(p: dict) -> bool:
    return bool(HOW_TO.search(p["text"])) or any("template" in t.lower() for t in p["tools"])


def onset(days: list[date]) -> int:
    """Where the how-to wave starts in the sorted days: the first post with at least two more
    in the next two days. One stray "prompt" post weeks earlier is not the wave."""
    for i, d in enumerate(days):
        if sum(1 for x in days[i:] if (x - d).days <= 2) >= 3:
            return i
    return 0


def verdict(how: list[date], first_ai: date | None, today: date) -> tuple[str, int | None, date | None]:
    """(label, days since the how-to wave began, the day it began)."""
    if not how:
        return ("还早" if first_ai else "看不出来"), None, None
    start = how[onset(how)]
    days = (today - start).days
    return ("窗口正开" if days <= OPEN_DAYS else "窗口在关" if days <= CLOSING_DAYS else "多半晚了"), days, start


def phrases(posts: list[dict], term: str, top: int = 3) -> list[str]:
    """Two- to five-word phrases at least three captions share that name the trend: what the
    site's pages should answer, in the posts' own words and languages."""
    name = {t for t in re.findall(r"[^\W_]+", base_name(term).lower()) if t not in ("ai", "ia")}
    counts: Counter = Counter()
    for p in posts:
        toks = re.findall(r"[^\W_]+", re.sub(r"https?://\S+|[@#][\w.]+", " ", p["text"].lower()))
        counts.update({" ".join(toks[i:i + n]) for n in range(2, 6) for i in range(len(toks) - n + 1)
                       if toks[i] not in STOP and toks[i + n - 1] not in STOP | END_STOP and len(toks[i]) > 1
                       and len(toks[i + n - 1]) > 1 and len(set(toks[i:i + n])) == n and set(toks[i:i + n]) & name})
    cands = {g: c for g, c in counts.items() if c >= 3 and not set(g.split()) <= name | {"ai", "ia"}}
    keep = sorted((g for g, c in cands.items() if not any(o != g and f" {g} " in f" {o} " and co >= 0.8 * c for o, co in cands.items())),
                  key=lambda g: (-cands[g], -len(g)))
    out: list[str] = []
    for g in keep:   # windows cut from one caption repeated word for word are one phrase
        a = set(g.split())
        if not any(len(a & set(o.split())) / len(a | set(o.split())) >= 0.5 for o in out):
            out.append(g)
    return out[:top]


def summarize(term: str, posts: list[dict], sounds: dict[str, dict], before: dict | None, today: date, now: datetime) -> dict:
    """The check's answer from the posts: verdict, dates, languages, tools, phrases, sounds."""
    named, posts = names_it(term), list({p["id"]: p for p in posts}.values())   # a post two queries found is one post
    mine = [p for p in posts if named(p) and p["day"]]
    ai = sorted(date.fromisoformat(p["day"]) for p in mine if p["views"] >= AI_VIEWS_MIN and is_ai(p))
    how = sorted(date.fromisoformat(p["day"]) for p in mine if p["views"] >= HOW_TO_VIEWS_MIN and is_how_to(p))
    label, days, start = verdict(how, ai[0] if ai else None, today)
    langs = Counter(p["lang"].split("-")[0].lower() for p in mine if p["lang"])
    total = sum(v for k, v in langs.items() if k in LANGS)
    tools = Counter(t for p in mine for t in tools_of(p))
    users = Counter((p["sound"] or {}).get("id") for p in mine if p["sound"])
    snd = []
    for s in sorted((s for s in sounds.values() if users.get(s["id"])), key=lambda s: -(s.get("videos") or 0))[:2]:
        rate = ""
        old = (before or {}).get("sounds", {}).get(s["id"])
        if old is not None and before.get("at"):
            hours = max(1.0, (now - datetime.fromisoformat(before["at"])).total_seconds() / 3600)
            rate = f",上次以来约每天 {((s.get('videos') or 0) - old) * 24 / hours:+,.0f}"
        snd.append(f"“{s['title'][:30]}”{(s.get('videos') or 0):,} 个视频{rate}")
    return {"label": label, "how_days": days, "how_start": start.isoformat() if start else "",
            "first_ai": ai[0].isoformat() if ai else "", "recent": sum(1 for d in how if (today - d).days <= 2),
            "before": sum(1 for d in how if 3 <= (today - d).days <= 5), "named": len(mine), "found": len(posts),
            "langs": " · ".join([f"{LANGS[k]} {v * 100 / total:.0f}%" for k, v in langs.most_common() if k in LANGS and v * 100 / total >= 5][:2]) if total else "",
            "tools": " · ".join(f"{t} {n}" for t, n in tools.most_common(2)), "phrases": phrases(mine, term), "sounds": snd,
            "sound_counts": {k: s.get("videos") for k, s in sounds.items()}}


def line(r: dict) -> str:
    """The check in one line for a lead's checks and note (no ｜ in it): '做站体检:窗口正开,教程/模版 11-01 起成批出现 2 天'."""
    md = lambda iso: f"{iso[5:7]}-{iso[8:10]}"   # noqa: E731
    text = {"还早": f"还早,AI 版 {md(r['first_ai'])} 已出现,教程还没成批出来" if r["first_ai"] else "还早",
            "看不出来": "看不出来,搜到的作品里没有 AI 版"}.get(r["label"])
    if text is None:
        text = f"{r['label']},教程/模版 {md(r['how_start'])} 起成批出现{'' if r['label'] == '窗口正开' else '已'} {r['how_days']} 天"
    if r["named"] < FEW:
        text += f",提到梗名的只有 {r['named']} 帖,仅供参考"
    return LABEL + text.replace("｜", "/")


def load(snaps: Path) -> dict:
    try:
        return json.loads((snaps / STATE).read_text())
    except (OSError, ValueError):
        return {}


def check(term: str, snaps: Path, today: date | None = None, now: datetime | None = None) -> tuple[dict, int]:
    """(the check's answer, cost in micro-USD) for one search term. A term checked in the last
    CACHE_HOURS gets that answer back for free."""
    now = now or datetime.now(timezone.utc)
    today = today or now.date()
    state = load(snaps)
    held = state.get(term)
    if held and now - datetime.fromisoformat(held["at"]) < timedelta(hours=CACHE_HOURS):
        return held["result"], 0
    data, cost = aisa.call_all(calls(term, today))
    posts = [p for cid, d in data.items() for p in read(cid, d)]
    named = names_it(term)
    shared = Counter((p["sound"] or {}).get("id") for p in posts if p["sound"] and named(p))
    follow = [sid for sid, n in shared.most_common(SOUNDS) if sid and n >= 2]
    sounds = {}
    if follow:
        got, c = aisa.call_all([{"call_id": f"sound:{sid}", "tool": TOOLS["sound"], "arguments": {"music_id": sid}} for sid in follow])
        cost += c
        for cid, d in got.items():
            info = d.get("data", d)
            m = (info.get("music_info") if isinstance(info, dict) else None) or _find(info, lambda x: "id_str" in x or "user_count" in x)
            m = m[0] if isinstance(m, list) and m else m
            if isinstance(m, dict):
                sounds[cid[6:]] = {"id": cid[6:], "title": m.get("title") or "", "videos": m.get("user_count")}
    result = summarize(term, posts, sounds, held, today, now)
    result["line"] = line(result)
    state[term] = {"at": now.isoformat(timespec="minutes"), "result": result, "sounds": result["sound_counts"]}
    cut = (now - timedelta(days=LOOKBACK_DAYS)).isoformat()
    state = {t: v for t, v in state.items() if v.get("at", "") >= cut}
    snaps.mkdir(parents=True, exist_ok=True)
    (snaps / STATE).write_text(json.dumps(state, ensure_ascii=False))
    return result, cost
