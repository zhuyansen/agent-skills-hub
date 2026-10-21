"""Radar signal ①d: new sites taking off on social media, found by the links people post.

A site that catches on is linked before it ranks. This step reads the external links in
the posts the radar already fetches every 8 hours (the X accounts in sources.json, through
source_signals.x_new) and in popular Bluesky posts (bluesky.py), reduces each link to its
registrable domain and keeps WINDOW_HOURS of who linked what in the snapshot dir. A domain
is a candidate when MIN_AUTHORS or more different people linked it in the window and RDAP
(free, meme_checks.rdap) says it was registered MAX_AGE_DAYS ago or less.

Left out: platforms and link shorteners (PLATFORMS: X, YouTube, GitHub, Hugging Face,
OpenAI, Anthropic, bit.ly...), a site on a host's subdomain (it reduces to the host, which
is old), institutions, our own sites (OWN_SITES), a site this step reported before, and
one the weekly new-site signal (new_sites.py) holds when its snapshot is in the same dir.
X gives links as t.co: each is expanded without following the redirect (a HEAD request,
then its Location; free), at most TCO_MAX a run TCO_PAUSE apart, cached in the snapshot.

With GOANYAPI_API_KEY each candidate (TRAFFIC_MAX a run) is tagged with where its visits
come from (GoAnyAPI `traffic` with three months of history: 2 credits, $0.002, October
2026): social-driven or search-driven, and its monthly visits. Without the key the
candidates are kept untagged.

Shadow mode (SOCIAL_SHOW off): a candidate becomes a lead of kind "social", named after
the site (the domain's label, lowercased: "altstream" for altstream.online), with the
posts that linked it as evidence. radar.py records it straight into radar_leads, so
review.py checks it in Google Trends 14 days later like any lead, and shows nothing of it
but one status line: no row in the mail, the picks or the keyword table, and no Jev.
"""
from __future__ import annotations

import gzip
import http.client
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import bluesky
import goanyapi
import meme_checks

# Off: candidates are recorded for the 14-day review and never shown. Turn it on only after
# the review shows this signal's hit rate ("①社交新站" in the daily report's hit-rate table);
# its leads then go through Jev's name check and into the reports like the other ① signals.
SOCIAL_SHOW = False

STATE = "social_sites.json.gz"
WINDOW_HOURS = 72
MIN_AUTHORS = 2
MAX_AGE_DAYS = 90
MIN_LABEL = 3              # a site name shorter than this names nothing
TOP = 10                   # candidates kept a run, most people linking first
POST_CHARS = 280
POSTS_KEPT = 10            # posts per candidate, most-liked first
REPORTED_DAYS = 180        # a site reported once is not reported again for this long
TCO_MAX = 60               # t.co expansions a run,
TCO_PAUSE = 0.25           # this many seconds apart,
TCO_BUDGET = 60            # within this many seconds
TCO_TIMEOUT = 15
TCO_KEEP_DAYS = 7
RDAP_MAX = 20              # RDAP lookups a run (rdap.org),
RDAP_PAUSE = 1.0           # this many seconds apart,
RDAP_BUDGET = 90           # within this many seconds
RDAP_KEEP_DAYS = 30        # a registration date is asked again after this long
RDAP_RETRY_DAYS = 1        # a lookup RDAP did not answer is tried again the next day
TRAFFIC_MAX = 10           # GoAnyAPI traffic lookups a run, $0.002 each
TRAFFIC_MONTHS = 3         # history asked for: 3 months is the cheapest mode (2 credits)
TRAFFIC_TIMEOUT = 30
TRAFFIC_BUDGET = 150       # seconds for all of a run's lookups
TRAFFIC_KEEP_DAYS = 7
UA = "agentskillshub-radar/1.0"
OWN_SITES = frozenset({"agentskillshub.top", "jasonzhu.ai"})
# Where people post and what they post with, not sites that take off: networks, video, code
# and model hosts, the big AI labs, shops, crowdfunding, link-in-bio pages, link shorteners,
# and hosts whose subdomains are other people's sites (a site there reduces to the host).
PLATFORMS = frozenset("""
x.com twitter.com t.co twimg.com pscp.tv periscope.tv youtube.com youtu.be ytimg.com youtube-nocookie.com
tiktok.com tiktokcdn.com instagram.com threads.net threads.com facebook.com fb.com fb.me fb.watch meta.com
messenger.com whatsapp.com wa.me reddit.com redd.it redditmedia.com linkedin.com lnkd.in
github.com github.io githubusercontent.com gitlab.com gitlab.io huggingface.co hf.co hf.space medium.com substack.com
google.com goo.gl g.co gstatic.com googleapis.com googleusercontent.com withgoogle.com blogspot.com forms.gle android.com
apple.com apple.co icloud.com microsoft.com bing.com live.com office.com azure.com msn.com aka.ms outlook.com
sharepoint.com xbox.com openai.com chatgpt.com sora.com oaistatic.com oaiusercontent.com anthropic.com claude.ai
claude.com x.ai grok.com
bit.ly bitly.com tinyurl.com ow.ly buff.ly dlvr.it ift.tt is.gd t.ly rebrand.ly cutt.ly shorturl.at rb.gy tiny.cc
s.id dub.sh trib.al spr.ly hubs.ly hubs.la amzn.to a.co amzn.eu linktr.ee beacons.ai bio.link lnk.bio linkin.bio
bsky.app bsky.social bsky.network mastodon.social joinmastodon.org discord.com discord.gg t.me telegram.org
twitch.tv kick.com pinterest.com pin.it tumblr.com snapchat.com spotify.com spoti.fi soundcloud.com bandcamp.com
patreon.com ko-fi.com kickstarter.com indiegogo.com gofundme.com amazon.com ebay.com etsy.com
wikipedia.org wikimedia.org archive.org archive.ph imgur.com giphy.com tenor.com klipy.com vimeo.com
producthunt.com ycombinator.com notion.so notion.site
vercel.app netlify.app pages.dev workers.dev web.app firebaseapp.com herokuapp.com onrender.com fly.dev railway.app
replit.app repl.co glitch.me streamlit.app gradio.live itch.io carrd.co wixsite.com squarespace.com wordpress.com
webflow.io framer.website framer.app lovable.app
""".split())
PLATFORM_TLDS = frozenset({"google", "youtube", "apple", "microsoft", "amazon", "gov", "edu", "mil", "int"})
# Second-level suffixes common enough to matter ("bbc.co.uk", not "co.uk"). Not the whole
# Public Suffix List: under one not listed, a site reduces to its registry, which RDAP calls old.
SUFFIXES_2 = frozenset("""
co.uk org.uk ac.uk gov.uk me.uk ltd.uk plc.uk com.au net.au org.au edu.au gov.au co.nz org.nz net.nz
co.jp ne.jp or.jp ac.jp go.jp com.cn net.cn org.cn gov.cn edu.cn com.hk com.tw org.tw idv.tw co.kr or.kr
com.sg com.my co.in net.in org.in co.id or.id com.ph com.vn co.th in.th com.pk com.br net.br org.br com.mx
com.ar com.co com.pe com.tr com.ua com.ru co.za com.ng com.eg com.sa co.il com.es com.pl co.at or.at
""".split())
SOURCE_KINDS = {"Search": "search", "SearchPaid": "search", "Social": "social", "SocialPaid": "social",
                "Direct": "direct", "Referrals": "referral", "Affiliate": "referral", "GenAI": "ai",
                "Mail": "mail", "DisplayAds": "ads"}
DRIVEN_ZH = {"social": "社交带量", "search": "搜索带量"}
NETWORK_ZH = {"x": "X", "bluesky": "Bluesky"}
_TCO = re.compile(r"https?://t\.co/[A-Za-z0-9]+")
KEYS = ("mentions", "rdap", "tco", "traffic", "reported")


# --- links and domains ------------------------------------------------------------------

def registrable(host: str) -> str:
    """'www.Altstream.online' -> 'altstream.online', 'news.bbc.co.uk' -> 'bbc.co.uk'; '' for
    an address or a bare name."""
    labels = host.lower().strip(".").split(".")
    if len(labels) < 2 or not all(labels) or labels[-1].isdigit():
        return ""
    keep = 3 if len(labels) >= 3 and ".".join(labels[-2:]) in SUFFIXES_2 else 2
    return ".".join(labels[-keep:])


def domain_of(url: str) -> str:
    try:
        return registrable(urllib.parse.urlsplit(url.strip()).hostname or "")
    except ValueError:
        return ""


def excluded(domain: str) -> bool:
    """A platform, a link shortener, an institution, one of our own sites, or a name too short."""
    return (domain in PLATFORMS or domain in OWN_SITES or domain.rsplit(".", 1)[-1] in PLATFORM_TLDS
            or len(domain.split(".")[0]) < MIN_LABEL)


def tweet_links(tweet: dict) -> list[str]:
    """A tweet's links: the full URLs X attached (entities.urls), then each t.co link of the
    text without one, to be expanded (expand())."""
    ents = [u for u in (tweet.get("entities") or {}).get("urls") or [] if isinstance(u, dict)]
    full = [u.get("expanded_url") or u.get("expandedUrl") or "" for u in ents]
    covered = {u.get("url") for u in ents if u.get("expanded_url") or u.get("expandedUrl")}
    short = [u for u in _TCO.findall(tweet.get("text") or "") if u not in covered]
    return list(dict.fromkeys(u for u in full + short if u))


class _Stay(urllib.request.HTTPRedirectHandler):
    """Report a redirect instead of following it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def location(short: str) -> str:
    """Where a t.co link points: the Location of its redirect, not followed; "" without one."""
    req = urllib.request.Request(short, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.build_opener(_Stay).open(req, timeout=TCO_TIMEOUT) as res:
            return res.headers.get("Location") or ""
    except urllib.error.HTTPError as exc:
        return exc.headers.get("Location") or ""


def expand(urls: list[str], cache: dict, today: date) -> tuple[int, int]:
    """Puts {"to", "day"} in `cache` for each t.co link of `urls` not there yet: at most TCO_MAX
    requests, TCO_PAUSE apart, within TCO_BUDGET seconds. A link that could not be reached is
    not cached, so a later run tries it again. Returns (asked, failed)."""
    todo = [u for u in dict.fromkeys(urls) if _TCO.fullmatch(u) and u not in cache][:TCO_MAX]
    asked = failed = 0
    end = time.monotonic() + TCO_BUDGET
    for u in todo:
        if time.monotonic() > end:
            break
        time.sleep(TCO_PAUSE if asked else 0)
        asked += 1
        try:
            cache[u] = {"to": location(u), "day": today.isoformat()}
        except (OSError, ValueError, http.client.HTTPException):
            failed += 1
    return asked, failed


# --- who linked what, over the window -------------------------------------------------------

def _when(text: str) -> datetime | None:
    try:
        at = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return at if at.tzinfo else at.replace(tzinfo=timezone.utc)


def x_posts(linked: list[dict], tco: dict) -> list[dict]:
    """X posts (x_new's `linked`) shaped like bluesky.make_post, each t.co link swapped for where
    it points ("" while it is not expanded)."""
    return [{"platform": "x", "author": p["account"], "url": p.get("url", ""), "text": " ".join(p.get("text", "").split()),
             "likes": int(p.get("likes") or 0), "at": p.get("created"),
             "links": [(tco.get(u) or {}).get("to", "") if _TCO.fullmatch(u) else u for u in p.get("links", [])]}
            for p in linked]


def mentions(posts: list[dict], since: datetime) -> list[dict]:
    """One row per post and site it links, for posts since `since`, sites left out dropped."""
    out = []
    for p in posts:
        at = p["at"] if isinstance(p["at"], datetime) else _when(p["at"] or "")
        if at is None or at < since or not p["author"]:
            continue
        out += [m for m in (_mention(p, link, at) for link in p["links"]) if m]
    return out


def _mention(p: dict, link: str, at: datetime) -> dict | None:
    domain = domain_of(link) if link else ""
    if not domain or excluded(domain):
        return None
    return {"domain": domain, "platform": p["platform"], "author": p["author"], "url": p["url"], "link": link,
            "text": p["text"][:POST_CHARS], "likes": p["likes"], "at": at.isoformat(), "date": at.date().isoformat()}


def update_window(window: dict[str, list[dict]], new: list[dict], since: datetime) -> dict[str, list[dict]]:
    """Mentions per domain over the window: old and new together, a post read again replaced by
    its newer copy (its likes move on), mentions from before `since` dropped."""
    keyed: dict[tuple, dict] = {}
    for m in [*(m for ms in window.values() for m in ms), *new]:
        at = _when(m.get("at", ""))
        if at is not None and at >= since:
            keyed[(m["domain"], m["url"] or f"{m['platform']}|{m['author']}|{m['text'][:80]}")] = m
    out: dict[str, list[dict]] = {}
    for m in keyed.values():
        out.setdefault(m["domain"], []).append(m)
    return out


def authors(ms: list[dict]) -> set[str]:
    """Who linked: one per account and network."""
    return {f"{m['platform']}:{m['author'].lower()}" for m in ms}


def linked_by_many(window: dict[str, list[dict]], skip: set[str]) -> list[str]:
    """Domains MIN_AUTHORS or more people linked in the window, most people first, then most likes."""
    many = [d for d, ms in window.items() if d not in skip and len(authors(ms)) >= MIN_AUTHORS]
    return sorted(many, key=lambda d: (-len(authors(window[d])), -sum(m["likes"] for m in window[d]), d))


# --- how old: RDAP ---------------------------------------------------------------------------

def check_rdap(domains: list[str], cache: dict, today: date) -> int:
    """Puts {"registered": "YYYY-MM-DD" or "", "ok", "checked"} in `cache` for the domains not
    known yet, or whose lookup is due again: at most RDAP_MAX lookups, RDAP_PAUSE apart,
    within RDAP_BUDGET seconds. Returns how many were looked up."""
    todo = [d for d in domains if _rdap_due(cache.get(d), today)][:RDAP_MAX]
    looked = 0
    end = time.monotonic() + RDAP_BUDGET
    for d in todo:
        if time.monotonic() > end:
            break
        time.sleep(RDAP_PAUSE if looked else 0)
        looked += 1
        cache[d] = _rdap_entry(_rdap(d), today)
    return looked


def _rdap(domain: str) -> dict:
    """meme_checks.rdap, which handles OSError and ValueError; a broken HTTP answer counts as none."""
    try:
        return meme_checks.rdap(_ascii(domain))
    except http.client.HTTPException:
        return {"domain": domain, "free": None, "registered": ""}


def _rdap_due(entry: dict | None, today: date) -> bool:
    if not entry:
        return True
    days = RDAP_KEEP_DAYS if entry.get("ok") else RDAP_RETRY_DAYS
    return entry.get("checked", "") <= (today - timedelta(days=days)).isoformat()


def _rdap_entry(found: dict, today: date) -> dict:
    """meme_checks.rdap's answer as kept. `ok` is False only when RDAP did not answer; a 404 for a
    domain people link means its registry has no RDAP, so its age stays unknown."""
    return {"registered": found.get("registered") or "", "ok": found.get("free") is not None, "checked": today.isoformat()}


def _ascii(domain: str) -> str:
    try:
        return domain.encode("idna").decode("ascii")
    except UnicodeError:
        return domain


def age_days(entry: dict | None, today: date) -> int | None:
    try:
        return (today - date.fromisoformat((entry or {}).get("registered", ""))).days
    except ValueError:
        return None


def is_new(entry: dict | None, today: date) -> bool:
    age = age_days(entry, today)
    return age is not None and 0 <= age <= MAX_AGE_DAYS


def candidate(domain: str, ms: list[dict], entry: dict, today: date) -> dict:
    who = authors(ms)
    return {"domain": domain, "registered": entry["registered"], "age": age_days(entry, today), "authors": len(who),
            "by": dict(Counter(a.split(":", 1)[0] for a in who)), "likes": sum(m["likes"] for m in ms),
            "mentions": sorted(ms, key=lambda m: -m["likes"])}


# --- where its visits come from: GoAnyAPI ------------------------------------------------------

def traffic_tag(data: dict) -> dict:
    """What a GoAnyAPI traffic answer says of a site: `driven`, "social" or "search" (whichever
    brings the larger share; "unknown" when neither has one), the shares by kind, the latest
    month's visits and the registration date it reports."""
    shares: dict[str, float] = {}
    for key, value in (data.get("TrafficSources") or {}).items():
        kind = SOURCE_KINDS.get(key, "other")
        shares[kind] = shares.get(kind, 0.0) + _num(value)
    months = sorted((data.get("EstimatedMonthlyVisits") or {}).items())
    social, search = shares.get("social", 0.0), shares.get("search", 0.0)
    return {"driven": "social" if social > search else "search" if search > social else "unknown",
            "shares": {k: round(v, 3) for k, v in sorted(shares.items(), key=lambda kv: -kv[1]) if v},
            "visits": round(_num(months[-1][1])) if months else None, "month": months[-1][0][:7] if months else "",
            "registered": str((data.get("DateData") or {}).get("registration") or "")[:10]}


def _num(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def tag_traffic(cands: list[dict], cache: dict, today: date) -> tuple[int, int, list[str]]:
    """Sets each candidate's `traffic` (traffic_tag) or `traffic_note` (why it has none): at most
    TRAFFIC_MAX lookups within TRAFFIC_BUDGET seconds, an answer reused for TRAFFIC_KEEP_DAYS.
    Without GOANYAPI_API_KEY nothing is asked. Returns (cost in micro-USD, lookups, errors)."""
    if not goanyapi.key():
        for c in cands:
            c["traffic_note"] = "没查流量(没有 GOANYAPI_API_KEY)"
        return 0, 0, []
    cost, asked, errors = 0, 0, []
    end = time.monotonic() + TRAFFIC_BUDGET
    for c in cands:
        if _reuse(c, cache, today):
            continue
        if asked >= TRAFFIC_MAX or time.monotonic() > end:
            c["traffic_note"] = "没查流量(本轮的流量查询额度已用完)"
            continue
        asked += 1
        spent, error = _lookup(c, cache, today)
        cost += spent
        errors += [error] if error else []
    return cost, asked, errors


def _reuse(c: dict, cache: dict, today: date) -> bool:
    held = cache.get(c["domain"])
    if not held or held.get("checked", "") < (today - timedelta(days=TRAFFIC_KEEP_DAYS)).isoformat():
        return False
    c["traffic"] = held["tag"]
    return True


def _lookup(c: dict, cache: dict, today: date) -> tuple[int, str]:
    try:
        data, cost = goanyapi.call("traffic", timeout=TRAFFIC_TIMEOUT, domain=_ascii(c["domain"]), month=TRAFFIC_MONTHS)
    except goanyapi.GoAnyError as exc:
        c["traffic_note"] = "流量查询失败"
        return 0, f"{c['domain']}: {exc}"
    c["traffic"] = traffic_tag(data)
    cache[c["domain"]] = {"tag": c["traffic"], "checked": today.isoformat()}
    return cost, ""


# --- the lead --------------------------------------------------------------------------------

def _count(n: int) -> str:
    return f"{n / 1e6:.1f}M" if n >= 1e6 else f"{n / 1e3:.0f}k" if n >= 1e3 else str(n)


def traffic_text(c: dict) -> str:
    t = c.get("traffic")
    if not t:
        return c.get("traffic_note", "没查流量")
    if t["driven"] == "unknown" and not t["visits"]:
        return "GoAnyAPI 还没有它的流量数据"
    split = f"社交 {t['shares'].get('social', 0):.0%}、搜索 {t['shares'].get('search', 0):.0%}"
    visits = f",约 {_count(t['visits'])} 访问/月({t['month']})" if t["visits"] else ""
    return f"{DRIVEN_ZH.get(t['driven'], '看不出靠什么带量')}({split}){visits}"


def note(c: dict) -> str:
    """'①社交新站 altstream.online:注册 61 天(2026-08-21),2 人链接(X 1、Bluesky 1);社交带量(社交 45%、搜索 12%),约 12k 访问/月(2026-09)'."""
    who = "、".join(f"{NETWORK_ZH.get(k, k)} {n}" for k, n in sorted(c["by"].items(), key=lambda kv: kv[0] != "x"))
    return (f"①社交新站 {c['domain']}:注册 {c['age']} 天({c['registered']}),{c['authors']} 人链接({who});"
            f"{traffic_text(c)}")


def lead(c: dict) -> dict:
    """A candidate as a radar lead, named after the site: the row radar.leads() reads from a
    block's `terms`, and the row review.record() writes (kinds, signals). Its evidence is the
    posts that linked the site (review.evidence())."""
    label, line = c["domain"].split(".")[0], note(c)
    posts = [{"url": m["url"], "account": m["author"], "text": m["text"], "likes": m["likes"], "date": m["date"],
              "platform": m["platform"], "link": m["link"]} for m in c["mentions"][:POSTS_KEPT]]
    return {"term": label, "kinds": ["social"], "signals": [line], "note": line, "recent": c["authors"],
            "variants": [label, c["domain"]], "posts": posts,
            "examples": [f"{c['domain']} · {c['authors']} 人链接", *(f"@{m['author']}: {m['text'][:80]}" for m in c["mentions"][:2])],
            "site": {"domain": c["domain"], "registered": c["registered"], "age_days": c["age"], "authors": c["authors"],
                     "by": c["by"], "traffic": c.get("traffic")}}


# --- the run ---------------------------------------------------------------------------------

def load(snaps: Path) -> dict:
    path = snaps / STATE
    try:
        held = json.loads(gzip.decompress(path.read_bytes())) if path.exists() else {}
    except (OSError, ValueError):
        held = {}
    return {k: held.get(k) or {} for k in KEYS}


def save(snaps: Path, state: dict, today: date) -> None:
    """The state, each cache cut to how long it is worth keeping."""
    def recent(d: dict, field: str, days: int) -> dict:
        cut = (today - timedelta(days=days)).isoformat()
        return {k: v for k, v in d.items() if (v.get(field, "") if isinstance(v, dict) else v) >= cut}
    state.update(tco=recent(state["tco"], "day", TCO_KEEP_DAYS), rdap=recent(state["rdap"], "checked", RDAP_KEEP_DAYS),
                 traffic=recent(state["traffic"], "checked", TRAFFIC_KEEP_DAYS),
                 reported=recent(state["reported"], "", REPORTED_DAYS))
    snaps.mkdir(parents=True, exist_ok=True)
    (snaps / STATE).write_bytes(gzip.compress(json.dumps(state, ensure_ascii=False).encode()))


def reported_elsewhere(snaps: Path) -> set[str]:
    """Domains the weekly new-site signal (new_sites.py) reported, when its snapshot is in this dir."""
    path = snaps / "new_sites.json.gz"
    try:
        return set(json.loads(gzip.decompress(path.read_bytes()))) if path.exists() else set()
    except (OSError, ValueError):
        return set()


def gather(linked: list[dict], state: dict, since: datetime, today: date) -> dict:
    """This run's mentions: the links of the X posts in the window (t.co expanded; retweets left
    out, as in source_signals.novel_names) and Bluesky's."""
    recent = [p for p in linked if isinstance(p.get("created"), datetime) and p["created"] >= since
              and not str(p.get("text", "")).startswith("RT @")]
    asked, failed = expand([u for p in recent for u in p.get("links", [])], state["tco"], today)
    sky = bluesky.posts(since)
    found = mentions(x_posts(recent, state["tco"]) + sky["posts"], since)
    return {"mentions": found, "x_posts": len(recent), "tco": {"asked": asked, "failed": failed},
            "bluesky": {k: v for k, v in sky.items() if k != "posts"} | {"linked": len(sky["posts"])}}


def find(state: dict, snaps: Path, today: date) -> dict:
    """The new sites in the window: MIN_AUTHORS or more people linked, registered MAX_AGE_DAYS ago or less."""
    window = state["mentions"]
    many = linked_by_many(window, set(state["reported"]) | reported_elsewhere(snaps))
    looked = check_rdap(many, state["rdap"], today)
    sites = [candidate(d, window[d], state["rdap"][d], today) for d in many if is_new(state["rdap"].get(d), today)]
    unknown = sum(1 for d in many if d in state["rdap"] and age_days(state["rdap"][d], today) is None)
    return {"domains": len(window), "many": len(many), "rdap_looked": looked, "rdap_unknown": unknown, "sites": sites[:TOP]}


def social_sites(snaps: Path, x_block: dict | None = None, now: datetime | None = None) -> dict:
    """One run. The block carries the leads as `terms` (into radar.leads()) when SOCIAL_SHOW is
    on, else as `shadow_leads`, which radar.record_shadow() writes to radar_leads unseen."""
    now = now or datetime.now(timezone.utc)
    today, since = now.date(), now - timedelta(hours=WINDOW_HOURS)
    state = load(snaps)
    read = gather((x_block or {}).get("linked") or [], state, since, today)
    state["mentions"] = update_window(state["mentions"], read["mentions"], since)
    found = find(state, snaps, today)
    cost, asked, errors = tag_traffic(found["sites"], state["traffic"], today)
    state["reported"].update({c["domain"]: today.isoformat() for c in found["sites"]})
    save(snaps, state, today)
    rows = [lead(c) for c in found["sites"]]
    return {"posts": read["x_posts"] + read["bluesky"]["linked"], "x_posts": read["x_posts"], "tco": read["tco"],
            "bluesky": read["bluesky"], **{k: found[k] for k in ("domains", "many", "rdap_looked", "rdap_unknown")},
            "sites": [{k: v for k, v in c.items() if k != "mentions"} for c in found["sites"]],
            "traffic": {"asked": asked, "key": bool(goanyapi.key())}, "errors": read["bluesky"]["errors"] + errors,
            "cost_micros": cost, "shadow": not SOCIAL_SHOW,
            "terms": rows if SOCIAL_SHOW else [], "shadow_leads": [] if SOCIAL_SHOW else rows}


# --- the status line ---------------------------------------------------------------------------

def status(b: dict) -> str:
    """The signal's line in the report's data status; in shadow mode the only trace of it."""
    label = "- ① 社交新站" + ("(影子模式,只记录不展示)" if b.get("shadow", not SOCIAL_SHOW) else "")
    if b.get("skipped") or b.get("error"):
        return f"{label}:{b.get('error') or '跳过'}"
    sky = b["bluesky"]
    read = (f"Bluesky 搜索 {sky['requests']} 次 {sky['read']} 帖" if sky["source"] == "search" else
            f"Bluesky 搜索被拒({sky['refused']}),改抽 Jetstream {sky['read']} 帖")
    line = (f"{label}:{len(b['sites'])} 个候选{_recorded(b)}(X 带链接帖 {b['x_posts']}、{read},"
            f"{WINDOW_HOURS} 小时内 {b['domains']} 个站、≥{MIN_AUTHORS} 人链接的 {b['many']} 个")
    line += f";流量查了 {b['traffic']['asked']} 个 ${b['cost_micros'] / 1e6:.3f}" if b["traffic"]["key"] else ";没有 GoAnyAPI key"
    return line + ")" + (";没取到:" + "、".join(b["errors"])[:200] if b["errors"] else "")


def _recorded(b: dict) -> str:
    """What radar.record_shadow() did with the run's candidates."""
    if not b.get("shadow") or not b["sites"]:
        return ""
    rec = b.get("recorded") or {}
    if rec.get("error") or rec.get("skipped"):
        return f",记录失败:{rec['error']}" if rec.get("error") else ",没记录(跳过数据库)"
    merged = f",{rec['merged']} 个已是别的信号的线索,只补了证据" if rec.get("merged") else ""
    return f",已记录 {rec.get('recorded', 0)} 个{merged}"
