"""Radar signal ②c: a new app climbing the App Store charts, and how much room is left.

Auday (watch recorder, released 2026-10-01) was #1 in Lifestyle (paid) in several
countries within days, before most of the talk about it on X. Two weeks later four
copies were out, and one of them (腕记 / WristMemo) took #2 in Productivity in China by
naming itself after what people type in App Store search ("手表录音", "watch voice
recorder"), not after itself. So for each young app on the charts this step asks three
things (luko/research/24-深度-Auday与腕记.md has the whole story):

  1. charts: Apple's RSS charts (free, no key) for COUNTRIES x paid/free x overall and
     GENRES. An app released in the last YOUNG_DAYS days that sits in a genre's top
     TOP_GENRE or the overall top TOP_ALL is a candidate; with yesterday's snapshot, so
     is one that entered a chart or rose JUMP places. The first day it shows it becomes a
     lead term (its name before the dash), like a breakout repo.
  2. search terms and crowding (free): the descriptive half of its name ("手表录音笔",
     "watch voice notes") through App Store search hints, which list what people type
     and other apps sold on the same words; then App Store search for those words,
     counting apps released in the last COPY_DAYS days (the copies) and where the app
     itself ranks. 0 copies: first mover; 1-3: room to follow; 4 or more: crowded.
  3. talk in China (AIsa, $0.01 a search): Xiaohongshu notes and Douyin videos of the
     last SOCIAL_DAYS days that name it, and posts like "Auday 火了之后，我把闪念做成了"
     (FOLLOW), which is where the copies announced themselves. Both searches return
     whatever they like for a word they do not know (腕记 on Douyin: esports and skin
     care), so only posts that hold the name count.

Steps 2 and 3 run for DEEP apps a day (new ones first, then any not read for RECHECK_DAYS);
the others show their last reading. DataForSEO's App Store keyword data was tried and
dropped (2026-10-19): it had no rows for Auday or 腕记, $0.012 each; a new app is not in
its index yet, which is exactly the case this signal is for.
"""
from __future__ import annotations

import gzip
import json
import plistlib
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import aisa
import memes

# storefront ids for the search hints endpoint (X-Apple-Store-Front)
COUNTRIES = {"us": "143441", "cn": "143465", "jp": "143462", "gb": "143444", "ca": "143455",
             "au": "143460", "de": "143443", "kr": "143466"}
COUNTRY_ZH = {"us": "美", "cn": "国区", "jp": "日", "gb": "英", "ca": "加", "au": "澳", "de": "德", "kr": "韩",
              "ae": "阿联酋", "br": "巴西", "ch": "瑞士", "es": "西", "fr": "法", "hk": "港", "id": "印尼", "in": "印度",
              "it": "意", "mx": "墨", "my": "马来", "nl": "荷", "ph": "菲", "pl": "波兰", "ru": "俄", "sa": "沙特",
              "se": "瑞典", "sg": "新加坡", "th": "泰", "tr": "土", "tw": "台", "vn": "越"}
# every storefront the charts below cover, for the search hints (X-Apple-Store-Front)
STOREFRONTS = {**COUNTRIES, "ae": "143481", "br": "143503", "ch": "143459", "es": "143454", "fr": "143442",
               "hk": "143463", "id": "143476", "in": "143467", "it": "143450", "mx": "143468", "my": "143473",
               "nl": "143452", "ph": "143474", "pl": "143478", "ru": "143469", "sa": "143479", "se": "143456",
               "sg": "143464", "th": "143475", "tr": "143480", "tw": "143470", "vn": "143471"}
# Apolu (apolu.app/charts) reads 30 storefronts every hour, Google Play and Mac included,
# and puts each chart in its page as JSON-LD (position, name, id). Apple's RSS above covers
# 8 storefronts with genres; Apolu adds Google Play, Mac and the other 22 storefronts'
# iPhone charts. Its robots.txt allows every agent but named AI crawlers; we read about 190
# pages once a day under our own name, and keep only ids and positions.
APOLU = "https://apolu.app/charts/{cc}/{chart}"
APOLU_CC = list(STOREFRONTS)
APOLU_CHARTS = {"iphone/free": "iPhone免费", "iphone/paid": "iPhone付费", "macos/free": "Mac免费", "macos/paid": "Mac付费",
                "android/free": "GP免费", "android/paid": "GP付费", "android/grossing": "GP畅销"}
APOLU_UA = "agentskillshub-radar/1.0 (+https://agentskillshub.top; daily, about 190 pages)"
GENRES = {"all": "总榜", "6012": "生活", "6007": "效率", "6002": "工具", "6013": "健康健美", "6008": "摄影录像"}
FEEDS = {"toppaidapplications": "付费", "topfreeapplications": "免费"}
LIMIT_ALL, LIMIT_GENRE = 200, 100
YOUNG_DAYS = 30
TOP_ALL, TOP_GENRE = 100, 20
JUMP = 15
SHOWN = 15
DEEP = 3                 # a run; it runs every 8 hours with the source signals, so nine a day
RECHECK_DAYS = 3
COPY_DAYS = 30
SEARCH_LIMIT = 50
TERMS_PER_APP = 3
GAMES = "6014"           # games are mostly console ports and a different trade: left out
CROWDED = 4
SOCIAL_DAYS = 14
FLAGGED_DAYS = 45
STATE = "appstore.json.gz"
XHS_TOOL = "get_tikhub_xiaohongshu_app_v2_search_notes"
DOUYIN_TOOL = "post_tikhub_douyin_search_fetch_video_search_v5"
# a post by someone who built the next one ("Auday 火了之后，我把闪念做成了"); "之后", "对比" and "vs"
# also caught a list of watch features and "同款" a sound-effects post (2026-10-19), so they are not here
FOLLOW = re.compile(r"火了|爆了|爆火|平替|替代品|竞品|我也做|也做了|另一种思路|做了一[个款]")
UA = "agentskillshub-radar/1.0"
WINDOW_ZH = {"first": "先手", "room": "还能跟", "crowded": "已经挤了"}


def _json(url: str, tries: int = 2) -> dict:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as res:
            return json.load(res)
    except (OSError, ValueError):
        if tries > 1:
            time.sleep(3)
            return _json(url, tries - 1)
        raise


def chart(key: str) -> list[dict]:
    """One chart, best first: [{id, name, release, price, artist, genre}]."""
    cc, feed, genre = key.split("/")
    limit = LIMIT_ALL if genre == "all" else LIMIT_GENRE
    url = f"https://itunes.apple.com/{cc}/rss/{feed}/limit={limit}" + ("" if genre == "all" else f"/genre={genre}") + "/json"
    entries = _json(url).get("feed", {}).get("entry") or []
    out = []
    for e in entries if isinstance(entries, list) else [entries]:
        price = e.get("im:price", {}).get("attributes", {})
        out.append({"id": e["id"]["attributes"]["im:id"], "name": e["im:name"]["label"],
                    "release": e.get("im:releaseDate", {}).get("label", "")[:10],
                    "price": f"{price.get('currency', '')} {float(price.get('amount') or 0):g}".strip(),
                    "artist": e.get("im:artist", {}).get("label", ""),
                    "genre": e.get("category", {}).get("attributes", {}).get("label", ""),
                    "genre_id": e.get("category", {}).get("attributes", {}).get("im:id", "")})
    return out


def keys() -> list[str]:
    return [f"{cc}/{feed}/{g}" for cc in COUNTRIES for feed in FEEDS for g in GENRES]


def apolu_keys() -> list[str]:
    """'br/a:android-free/all'. iPhone charts only where Apple's RSS does not already read them."""
    return [f"{cc}/a:{c.replace('/', '-')}/all" for cc in APOLU_CC for c in APOLU_CHARTS
            if not (c.startswith("iphone") and cc in COUNTRIES)]


def apolu_chart(key: str) -> list[dict]:
    cc, feed, _ = key.split("/")
    url = APOLU.format(cc=cc, chart=feed[2:].replace("-", "/"))
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": APOLU_UA}), timeout=30) as res:
        page = res.read().decode("utf-8", "replace")
    m = re.search(r'<script type="application/ld\+json">(\{"@context":"https://schema.org","@type":"ItemList".*?)</script>', page)
    if not m:
        raise ValueError("no chart list in the page")
    platform = "android" if "android" in feed else "mac" if "macos" in feed else "ios"
    return [{"id": e["url"].rstrip("/").rsplit("/", 1)[-1], "name": e.get("name", ""), "release": "", "price": "",
             "artist": "", "genre": "", "genre_id": "", "platform": platform}
            for e in sorted(json.loads(m.group(1)).get("itemListElement", []), key=lambda e: e.get("position", 999))]


def lookup(ids: list[str], cc: str) -> dict[str, dict]:
    """Release date, genre, maker and price for App Store ids (Apple's lookup, free, 150 a call)."""
    out = {}
    for i in range(0, len(ids), 150):
        url = f"https://itunes.apple.com/lookup?id={','.join(ids[i:i + 150])}&country={cc}"
        for r in _json(url).get("results", []):
            out[str(r["trackId"])] = {"release": r.get("releaseDate", "")[:10], "genre_id": str(r.get("primaryGenreId", "")),
                                      "genre": r.get("primaryGenreName", ""), "artist": r.get("artistName", ""),
                                      "price": f"{r.get('currency', '')} {float(r.get('price') or 0):g}".strip()}
    return out


def fill(charts: dict[str, list[dict]], state: dict, today: date) -> tuple[dict, dict]:
    """Apolu rows have no dates. Apple apps: looked up once and kept (`release`). Google
    Play has no public release date, so an app's first day on any chart we read stands in
    for it (`gp_first`); the apps on the first day's charts are the baseline, never young."""
    known = dict(state.get("release", {}))
    gp = dict(state.get("gp_first", {}))
    baseline = not gp
    todo: dict[str, set] = {}
    for key, rows in charts.items():
        cc = key.split("/")[0]
        for r in rows:
            if r.get("platform") == "android":
                gp.setdefault(r["id"], "base" if baseline else today.isoformat())
            elif r.get("platform") and r["id"] not in known:
                todo.setdefault(cc, set()).add(r["id"])
    for cc, ids in todo.items():
        ids -= set(known)
        if ids:
            got = _try(lookup, sorted(ids), cc)
            if isinstance(got, dict):
                known.update(got)
                known.update({i: {} for i in ids if i not in got})   # not in that store: do not ask again
    for rows in charts.values():
        for r in rows:
            if r.get("platform") == "android":
                r["release"] = "" if gp[r["id"]] == "base" else gp[r["id"]]
            elif r.get("platform"):
                r.update({k: v for k, v in known.get(r["id"], {}).items() if v})
    return known, gp


def label(key: str) -> str:
    cc, feed, genre = key.split("/")
    if feed.startswith("a:"):
        return f"{COUNTRY_ZH.get(cc, cc)}{APOLU_CHARTS[feed[2:].replace('-', '/')]}"
    return f"{COUNTRY_ZH[cc]}{GENRES[genre]}{FEEDS[feed]}"


def split_name(name: str) -> tuple[str, str]:
    """'腕记 - 手表录音笔·语音转文字' -> ('腕记', '手表录音笔·语音转文字'); 'Voday -AI daily' too."""
    parts = re.split(r"\s*[-–—|｜]\s+|\s+[-–—|｜]\s*|\s*[:：]\s*", name, maxsplit=1)
    return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")


def phrases(desc: str) -> list[str]:
    """The descriptive half cut into what someone might type: '手表录音笔·语音转文字' ->
    ['手表录音笔', '语音转文字']; 'Watch Voice Notes & AI' -> ['watch voice notes']."""
    out = []
    for p in re.split(r"[·•,，、&+/|｜()（）]| and | with | for ", desc.lower()):
        p = " ".join(re.sub(r"(?<![a-z])(ai|app|pro|plus)(?![a-z])", " ", p).split())
        p = re.sub(r"(?<=[\u4e00-\u9fff]) (?=[\u4e00-\u9fff])", "", p)   # 'watch全天 录音' -> 'watch全天录音'
        words = p.split()
        # 'all-day watch recorder' is its own; 'watch recorder' is what people type
        for q in [p, " ".join(words[-2:])] if len(words) > 2 else [p]:
            if 2 <= len(q) <= 40 and q not in out:
                out.append(q)
    return out


def young(app: dict, today: date) -> int | None:
    try:
        days = (today - date.fromisoformat(app["release"])).days
    except ValueError:
        return None
    return days if 0 <= days <= YOUNG_DAYS else None


def candidates(charts: dict[str, list[dict]], before: dict[str, list[str]], today: date) -> list[dict]:
    """Young apps on any chart, with every place they hold; strongest first."""
    apps: dict[str, dict] = {}
    for key, rows in charts.items():
        prev = {i: n + 1 for n, i in enumerate(before.get(key) or [])}
        top = TOP_ALL if key.endswith("/all") else TOP_GENRE
        for n, a in enumerate(rows, 1):
            days = young(a, today)
            if days is None or a["genre_id"] == GAMES:
                continue
            was = prev.get(a["id"])
            entered = bool(before.get(key)) and was is None
            jumped = was is not None and was - n >= JUMP
            if n > top and not (entered or jumped):
                continue
            app = apps.setdefault(a["id"], {**a, "days": days, "places": [], "names": {}})
            app["names"].setdefault(key.split("/")[0], a["name"])
            app["places"].append({"chart": key, "rank": n, "was": was, "entered": entered})
    for app in apps.values():
        app["places"].sort(key=lambda p: (p["rank"], p["chart"].endswith("/all")))
        app["countries"] = sorted({p["chart"].split("/")[0] for p in app["places"]})
        app["home"] = app["places"][0]["chart"].split("/")[0]
        app["name"] = app["names"][app["home"]]   # the name it sells under where it ranks best
        app["brand"], app["desc"] = split_name(app["name"])
    return sorted(apps.values(), key=lambda a: (-len(a["countries"]), a["places"][0]["rank"], -len(a["places"])))


def hints(term: str, cc: str) -> list[str]:
    """App Store search suggestions for a prefix, as the store shows them."""
    url = ("https://search.itunes.apple.com/WebObjects/MZSearchHints.woa/wa/hints?clientApplication=Software&term="
           + urllib.parse.quote(term))
    req = urllib.request.Request(url, headers={"X-Apple-Store-Front": f"{STOREFRONTS[cc]}-1,29", "User-Agent": "AppStore/3.0 iOS/17.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return [h["term"] for h in plistlib.loads(res.read()).get("hints", [])]
    except (OSError, ValueError, plistlib.InvalidFileException):
        return []


def search(term: str, cc: str, entity: str = "software") -> list[dict]:
    url = (f"https://itunes.apple.com/search?term={urllib.parse.quote(term)}&country={cc}"
           f"&entity={entity}&limit={SEARCH_LIMIT}")
    return [{"id": str(r["trackId"]), "name": r["trackName"], "release": r.get("releaseDate", "")[:10]}
            for r in _json(url).get("results", [])]


def crowding(app: dict, today: date) -> dict:
    """The words it is sold on, where it ranks for them, and the other new apps on them."""
    # no descriptive half ('Open Screen Sharing'): the name is the description
    cc, words = app["home"], phrases(app["desc"] or app["brand"])[:TERMS_PER_APP]
    suggested, terms, copies = [], [], {}
    for w in words:
        for h in hints(w, cc):
            if h not in suggested and h != w:
                suggested.append(h)
        found = search(w, cc, "macSoftware" if app.get("platform") == "mac" else "software")
        rank = next((n for n, r in enumerate(found, 1) if r["id"] == app["id"]), None)
        terms.append({"term": w, "rank": rank})
        for r in found:
            try:
                fresh = (today - date.fromisoformat(r["release"])).days <= COPY_DAYS
            except ValueError:
                fresh = False
            if fresh and r["id"] != app["id"]:
                copies.setdefault(r["id"], {"name": r["name"], "release": r["release"]})
    n = len(copies)
    window = "first" if n == 0 else "crowded" if n >= CROWDED else "room"
    return {"country": cc, "terms": terms, "hints": suggested[:8], "copies": list(copies.values()), "window": window}


def _since(today: date) -> int:
    return int(datetime.combine(today - timedelta(days=SOCIAL_DAYS), datetime.min.time(), timezone.utc).timestamp())


def _holds(text: str, name: str) -> bool:
    return name.lower() in text.lower()


def xhs(name: str, today: date) -> tuple[dict, int]:
    data, cost = aisa.call([{"call_id": "x", "tool": XHS_TOOL, "arguments": {
        "keyword": name, "sort_type": "popularity_descending", "time_filter": "一周内"}}])
    items = (((data.get("x") or {}).get("data") or {}).get("data") or {}).get("items") or []
    since, posts = _since(today), []
    for it in items:
        n = it.get("note") or {}
        if not n or int(n.get("timestamp") or 0) < since:
            continue
        text = f"{n.get('title', '')} {n.get('desc', '')}"
        posts.append({"title": (n.get("title") or n.get("desc", "")[:30]).strip(), "likes": int(n.get("liked_count") or 0),
                      "author": (n.get("user") or {}).get("nickname", ""), "url": f"https://www.xiaohongshu.com/explore/{n['id']}",
                      "names": _holds(text, name), "follow": bool(FOLLOW.search(text))})
    return _social(posts), cost


def douyin(name: str, today: date) -> tuple[dict, int]:
    data, cost = aisa.call([{"call_id": "d", "tool": DOUYIN_TOOL, "arguments": {"body": {"keyword": name}}}])
    items = ((data.get("d") or {}).get("data") or {}).get("items") or []
    since, posts = _since(today), []
    for it in items:
        a = it.get("aweme_info") or {}
        if int(a.get("create_time") or 0) < since:
            continue
        text = a.get("desc", "")
        posts.append({"title": " ".join(text.split())[:40], "likes": int((a.get("statistics") or {}).get("digg_count") or 0),
                      "author": (a.get("author") or {}).get("nickname", ""),
                      "url": f"https://www.douyin.com/video/{a.get('aweme_id', '')}",
                      "names": _holds(text, name), "follow": bool(FOLLOW.search(text))})
    return _social(posts), cost


def _social(posts: list[dict]) -> dict:
    """Posts that name the app, and follow-ups (recent posts in the results that read like
    'X took off, so I built Y', named or not)."""
    named = sorted((p for p in posts if p["names"]), key=lambda p: -p["likes"])
    follow = sorted((p for p in posts if p["follow"]), key=lambda p: -p["likes"])
    return {"posts": len(named), "likes": sum(p["likes"] for p in named), "top": named[:2], "follow": follow[:3]}


def read(app: dict, today: date) -> tuple[dict, int, list[str]]:
    """Steps 2 and 3 for one app. A failed source leaves the others standing."""
    out, cost, errors = {"date": today.isoformat()}, 0, []
    try:
        if app.get("platform") != "android":   # Google Play has no open search to count copies in
            out["crowding"] = crowding(app, today)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{app['brand']} App Store 搜索:{type(exc).__name__}")
    for key, fn in (("xhs", xhs), ("douyin", douyin)):
        try:
            out[key], c = fn(app["brand"], today)
            cost += c
        except Exception as exc:  # noqa: BLE001 — no key, no credit, a timeout
            errors.append(f"{app['brand']} {'小红书' if key == 'xhs' else '抖音'}:{' '.join(str(exc).split())[:80]}")
    return out, cost, errors


def load(snaps: Path) -> dict:
    path = snaps / STATE
    return json.loads(gzip.decompress(path.read_bytes())) if path.exists() else {}


def save(snaps: Path, state: dict) -> None:
    snaps.mkdir(parents=True, exist_ok=True)
    (snaps / STATE).write_bytes(gzip.compress(json.dumps(state, ensure_ascii=False).encode()))


def apps(snaps: Path, today: date | None = None, social: bool = True, apolu: bool = True) -> dict:
    today = today or date.today()
    state = load(snaps)
    with ThreadPoolExecutor(8) as pool:
        got = dict(zip(keys(), pool.map(lambda k: _try(chart, k), keys())))
    if apolu:
        with ThreadPoolExecutor(4) as pool:   # about 190 pages; four at a time is polite enough
            got.update(zip(apolu_keys(), pool.map(lambda k: _try(apolu_chart, k), apolu_keys())))
    charts = {k: v for k, v in got.items() if isinstance(v, list)}
    release, gp_first = fill(charts, state, today)
    failed = [k for k, v in got.items() if not isinstance(v, list)]
    if not charts:
        raise RuntimeError(f"all {len(got)} charts failed: {got[failed[0]]}")
    before = state.get("charts", {}) if state.get("date") != today.isoformat() else state.get("before", {})
    found = candidates(charts, before, today)[:SHOWN]

    cutoff = (today - timedelta(days=FLAGGED_DAYS)).isoformat()
    flagged = {i: d for i, d in state.get("flagged", {}).items() if d >= cutoff}
    checked = {i: c for i, c in state.get("checked", {}).items() if c.get("date", "") >= cutoff}
    recheck = (today - timedelta(days=RECHECK_DAYS)).isoformat()
    due = sorted((a for a in found if a["id"] not in checked or checked[a["id"]]["date"] <= recheck),
                 key=lambda a: a["id"] in checked)[:DEEP]
    cost, errors, client = 0, [], memes.jev()
    for a in due:
        if not social:
            res, c, err = {"date": today.isoformat()}, 0, []
            try:
                if a.get("platform") != "android":
                    res["crowding"] = crowding(a, today)
            except Exception as exc:  # noqa: BLE001
                err.append(f"{a['brand']} App Store 搜索:{type(exc).__name__}")
        else:
            res, c, err = read(a, today)
        # Jev: could a small team build for the need this app proved? (memes.APP_OPPORTUNITY)
        cr = res.get("crowding") or {}
        res["score"] = memes.opportunity(client, {"app": f"{a['name']} ({a['genre']}, {a['price']})", "released_days_ago": a["days"],
                                                  "charts": [_place(p) for p in a["places"][:4]],
                                                  "search_words": [t["term"] for t in cr.get("terms", [])],
                                                  "copies": [c["name"] for c in cr.get("copies", [])]}, memes.APP_OPPORTUNITY)
        checked[a["id"]] = res
        cost += c
        errors += err

    terms = []
    for a in found:
        a["reading"] = checked.get(a["id"])
        a["new"] = a["id"] not in flagged
        if a["new"]:
            flagged[a["id"]] = today.isoformat()
            p = a["places"][0]
            rd, cr = a["reading"] or {}, (a["reading"] or {}).get("crowding") or {}
            # `named` carries Jev's opportunity score, as for memes: radar.judge() skips these rows,
            # radar_leads keeps it, and the daily picks read it back with `what`
            terms.append({"term": a["brand"].lower(), "recent": len(a["places"]), "named": rd.get("score"),
                          "what": f"新应用,{_place(p)},上架 {a['days']} 天" + (
                              f",卖点词 {'、'.join(t['term'] for t in cr.get('terms', []))},同类新应用 {len(cr.get('copies', []))} 个"
                              f"({WINDOW_ZH[cr['window']]})" if cr else ""),
                          "window": cr.get("window"),
                          # no descriptive half in the name (오리집, 해병PTSD알람): its "selling words" are
                          # its own name, so the crowding count says nothing; not a pick (radar.picks)
                          "described": bool(a["desc"]),
                          # the daily picks only get this note back from radar_leads, so it says the window too
                          "note": f"②榜单 {label(p['chart'])} #{p['rank']}(上架 {a['days']} 天,{len(a['countries'])} 个区上榜)"
                                  + (f",{WINDOW_ZH[cr['window']]}" if cr else "")
                                  + ("" if a["desc"] else ",无卖点词"),
                          "examples": [a["name"], a["artist"], a["genre"]], "variants": [a["brand"].lower()]})
    save(snaps, {"date": today.isoformat(), "charts": {k: [r["id"] for r in v] for k, v in charts.items()},
                 "before": before, "flagged": flagged, "checked": checked, "release": release, "gp_first": gp_first})
    return {"today": today.isoformat(), "charts": len(charts), "failed": failed, "gp_baseline": gp_first and
            all(v == "base" for v in gp_first.values()), "first_run": not before, "apps": found, "terms": terms,
            "read": [a["brand"] for a in due], "errors": errors, "cost_micros": cost}


def _try(fn, *args):
    try:
        return fn(*args)
    except Exception as exc:  # noqa: BLE001
        return f"{type(exc).__name__}: {exc}"


def _place(p: dict) -> str:
    move = "🆕" if p["entered"] else (f"↑{p['was'] - p['rank']}" if p["was"] and p["was"] > p["rank"] else "")
    return f"{label(p['chart'])} #{p['rank']}{move}"


def _social_cell(s: dict | None) -> str:
    if not s:
        return "—"
    if not s["posts"]:
        return "0"
    return f"{s['posts']} 条 ♥{s['likes']}"


def section(b: dict) -> list[str]:
    """The report section, in Chinese like the rest of the mail."""
    lines = ["", f"### ② 应用跟进窗口(App Store / Mac / Google Play 30 个区;上架 ≤{YOUNG_DAYS} 天、冲进分类前 {TOP_GENRE} "
             f"或总榜前 {TOP_ALL} 的新应用,Google Play 按第一次上榜算;🆕 = 第一次出现,进上面的候选词)", ""]
    if b.get("skipped"):
        return []
    if b.get("error"):
        return lines + [f"失败:{b['error']}"]
    found = b.get("apps") or []
    if not found:
        return lines + [f"今天没有符合条件的新应用({b['charts']} 个榜单)"]
    lines += ["| 应用 | 上榜位置 | 上架 | 价格 | 卖点词(自己排第几) | App Store 联想 | 近 30 天同类新应用 | 窗口 | Jev 机会 | 小红书 | 抖音 |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in found:
        r = a.get("reading") or {}
        cr = r.get("crowding") or {}
        places = "<br>".join(_place(p) for p in a["places"][:4]) + (f"<br>…共 {len(a['places'])} 处" if len(a["places"]) > 4 else "")
        terms = "<br>".join(f"{t['term']}({t['rank'] or '50 名外'})" for t in cr.get("terms", [])) or "—"
        copies = cr.get("copies") or []
        copy_cell = (f"{len(copies)}" + ("：" + "、".join(c["name"].split(" - ")[0][:16] for c in copies[:4]) if copies else "")) if cr else "—"
        window = f"**{WINDOW_ZH[cr['window']]}**" if cr else "—"
        stale = f"<br>({r['date'][5:]} 读)" if r.get("date") and r["date"] != (b.get("today") or r["date"]) else ""
        link = (f"https://play.google.com/store/apps/details?id={a['id']}" if a.get("platform") == "android"
                else f"https://apps.apple.com/{a['home']}/app/id{a['id']}")
        lines.append(f"| {'🆕 ' if a['new'] else ''}[{a['name'][:40]}]({link}) | "
                     f"{places} | {a['release'][5:]}({a['days']} 天) | {a['price']} | {terms} | "
                     f"{'、'.join(cr.get('hints', [])[:5]) or '—'} | {copy_cell} | {window}{stale} | "
                     f"{'—' if r.get('score') is None else ('**%.2f**' if r['score'] >= memes.OPPORTUNITY_MIN else '%.2f') % r['score']} | "
                     f"{_social_cell(r.get('xhs'))} | {_social_cell(r.get('douyin'))} |".replace("\n", " "))
    lines += ["", f"窗口:按卖点词在 App Store 搜前 {SEARCH_LIMIT} 名里、近 {COPY_DAYS} 天上架的其他应用数:0 = 先手,1–3 = 还能跟,"
              f"≥{CROWDED} = 已经挤了。卖点词取应用名破折号后面那半(腕记就是靠“手表录音”这类词冲上去的)。"
              f"小红书/抖音只数近 {SOCIAL_DAYS} 天、正文里带应用名的帖子。"]
    said = []
    for a in found:
        r = a.get("reading") or {}
        for key, where in (("xhs", "小红书"), ("douyin", "抖音")):
            s = r.get(key) or {}
            said += [f"- **{a['brand']}** · {where} · {p['author']} ♥{p['likes']} · [{p['title'][:40] or '原帖'}]({p['url']})"
                     for p in s.get("top", [])[:1]]
            said += [f"- **{a['brand']}** · {where}跟风帖 · {p['author']} ♥{p['likes']} · [{p['title'][:40] or '原帖'}]({p['url']})"
                     for p in s.get("follow", []) if not p["names"] or p not in s.get("top", [])][:2]
    if said:
        lines += ["", "讨论和跟风帖:", *said]
    return lines


def status(b: dict) -> str:
    if b.get("skipped"):
        return "- ② 榜单:跳过"
    if b.get("error"):
        return f"- ② 榜单:{b['error']}"
    s = f"- ② 榜单:{b['charts']} 个榜单,{len(b['apps'])} 个新应用,今天细读 {', '.join(b['read']) or '无'}"
    if b.get("first_run"):
        s += ",首次运行,没有昨天的名次"
    if b.get("gp_baseline"):
        s += ",Google Play 今天是底子(没有上架日期,从明天起按第一次上榜算新应用)"
    if b.get("failed"):
        s += f";{len(b['failed'])} 个榜单没取到"
    if b.get("errors"):
        s += ";" + "; ".join(b["errors"][:4])
    return s


if __name__ == "__main__":
    # python ops/radar/appstore.py <snapshot-dir> [--no-social]: the section alone, for a dry run
    res = apps(Path(sys.argv[1]), social="--no-social" not in sys.argv)
    print("\n".join(section(res)))
    print(status(res), f"${res['cost_micros'] / 1e6:.3f}")
