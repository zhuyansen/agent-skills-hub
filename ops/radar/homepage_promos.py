"""Shadow record of what ten AI video and image sites link to from their own homepages (migration 044):
once a day (the UTC day), one row per link to the site itself, in the order the page first shows it,
with its label and whether it sits in the header, the body or the footer. Nothing shows it.

Why: a big site gives its homepage slots to its own feature and template pages by its own usage and
revenue data, so a page that keeps its slot for weeks is one that earns (a new model's first days there
are a launch slot, not proof). Demand shows in data like this before it shows in words (a share the
user passed on, 2026-10-31). The user chose this option (A: read the homepage HTML, keep the order of
its links) over a model reading each page (B) or a real browser on the user's Mac (C), and named the
ten sites. A site that cannot be read is left out: Leonardo answers 403 with a Cloudflare challenge,
which this does not try to get past, and some homepages build their banners in the browser, which the
HTML does not hold.

A review on 11-28 checks whether these slots show the trends the radar finds (memes.py) before their
posts do, and how long a slot lasts against what the trend earned; only then may it replace the
comments' "x% want their own" in the mail (meme_checks.intent). Free: about ten pages a day, read once
a day by the first 8-hourly source run that reaches them (robots.txt lets any crawler read "/" on all
ten, 10-31).
"""
from __future__ import annotations

import http.client
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

SITES = (  # (site, homepage); a link counts as the site's own on the homepage's domain and its subdomains
    ("pollo.ai", "https://pollo.ai/"),
    ("pixverse.ai", "https://pixverse.ai/"),
    ("hailuoai.video", "https://hailuoai.video/"),
    ("kling.ai", "https://kling.ai/"),                      # klingai.com redirects here
    ("vidu.com", "https://www.vidu.com/"),
    ("higgsfield.ai", "https://higgsfield.ai/"),
    ("dreamina.capcut.com", "https://dreamina.capcut.com/"),  # its own links include www.capcut.com
    ("krea.ai", "https://www.krea.ai/"),
    ("leonardo.ai", "https://leonardo.ai/"),
    ("seaart.ai", "https://www.seaart.ai/"),
)
UA = "agentskillshub-radar/1.0 (+https://agentskillshub.top)"
LANGUAGE = "en-US,en;q=0.9"   # the English homepage: without it PixVerse sent a Thai IP to /th (10-31)
TIMEOUT = 30
WORKERS = 5
MAX_BYTES = 5_000_000         # the largest of the ten was about 1.2 MB (Krea, 10-31)
MAX_LINKS = 300               # Pollo shows about 200 of its own
LABEL_MAX = 120
REPEATS = (3, 2)              # Krea prints each menu label three times ("Home Home Home")
AREAS = ("header", "nav", "footer")
HIDDEN = ("script", "style", "noscript", "template")
DONE = "SELECT DISTINCT site FROM radar_homepage_links WHERE day = :day"
INSERT = """
INSERT INTO radar_homepage_links (day, site, position, link, label, area)
VALUES (:day, :site, :position, :link, :label, :area)
ON CONFLICT (day, site, link) DO NOTHING
"""


class _Links(HTMLParser):
    """The page's links in order: (href, area, the words inside it: text, image alt, aria-label)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str, str]] = []
        self.open: Counter = Counter()
        self.cur: tuple[str, str, list[str]] | None = None

    def area(self) -> str:
        if self.open["footer"]:
            return "footer"
        return "nav" if self.open["header"] or self.open["nav"] else "body"

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in AREAS or tag in HIDDEN:
            self.open[tag] += 1
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self._close()   # an <a> left open ends where the next one starts
            self.cur = (a["href"], self.area(), [a.get("aria-label") or a.get("title") or ""])
        elif tag == "img" and self.cur:
            self.cur[2].append(a.get("alt") or "")

    def handle_endtag(self, tag: str) -> None:
        if (tag in AREAS or tag in HIDDEN) and self.open[tag]:
            self.open[tag] -= 1
        if tag == "a":
            self._close()

    def handle_data(self, data: str) -> None:
        if self.cur and not any(self.open[t] for t in HIDDEN):
            self.cur[2].append(data)

    def _close(self) -> None:
        if self.cur:
            self.links.append((self.cur[0], self.cur[1], " ".join(self.cur[2])))
        self.cur = None


def label_of(text: str) -> str:
    """The link's words, once."""
    words = text.split()
    for times in REPEATS:
        n = len(words) // times
        if n and len(words) == n * times and words == words[:n] * times:
            words = words[:n]
            break
    return " ".join(words)[:LABEL_MAX]


def key_of(href: str, page: str, domain: str) -> str | None:
    """A link to the site itself as kept: its path on the homepage's host, host + path on another host of
    its domain; None for other sites, mailto:, javascript: and the like. Query and fragment are dropped."""
    try:
        url = urlsplit(urljoin(page, href.strip()))
        host = (url.hostname or "").lower()
    except ValueError:   # a malformed address, such as an unclosed [ in the host
        return None
    if url.scheme not in ("http", "https") or not (host == domain or host.endswith("." + domain)):
        return None
    return (url.path or "/") if host == urlsplit(page).hostname else host + (url.path or "/")


def rows_of(day: date, site: str, page: str, html: str) -> list[dict]:
    """One row per link to the site itself, at the place the page first shows it (1-based), with the
    first label it has and the area of that first showing. page: the homepage's address after redirects."""
    parser = _Links()
    parser.feed(html)
    parser.close()
    parser._close()
    domain = ".".join((urlsplit(page).hostname or "").split(".")[-2:])
    kept: dict[str, dict] = {}
    for href, area, text in parser.links:
        key = key_of(href, page, domain)
        if key is not None:
            row = kept.setdefault(key, {"day": day, "site": site, "position": len(kept) + 1, "link": key,
                                        "label": "", "area": area})
            row["label"] = row["label"] or label_of(text)
    return list(kept.values())[:MAX_LINKS]


def fetch(url: str) -> tuple[str, str]:
    """The homepage's address after redirects, and its HTML (all ten serve UTF-8)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html", "Accept-Language": LANGUAGE})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
        return res.geturl(), res.read(MAX_BYTES).decode("utf-8", "replace")


def read_site(day: date, site: str, url: str) -> dict:
    """One site's rows, or why there are none; the next run of the day tries a site that failed again."""
    try:
        page, html = fetch(url)
    except urllib.error.HTTPError as exc:
        return {"site": site, "failed": f"HTTP {exc.code}"}
    except (OSError, http.client.HTTPException) as exc:   # URLError and timeouts are OSErrors
        return {"site": site, "failed": type(exc).__name__}
    rows = rows_of(day, site, page, html)
    return {"site": site, "rows": rows} if rows else {"site": site, "failed": "没有链接"}


def _done(engine, day: date) -> set[str]:
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL statement_timeout = '30s'"))
        return {row[0] for row in conn.execute(text(DONE), {"day": day})}


def _write(engine, rows: list[dict]) -> None:
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL statement_timeout = '60s'"))
        conn.execute(text(INSERT), rows)


def record(now: datetime | None = None) -> dict:
    """Keeps today's links of each site not kept yet today. Called with the radar's --skip-db honoured."""
    import review
    engine = review._engine()
    try:
        return _record(engine, (now or datetime.now(timezone.utc)).date())
    finally:
        engine.dispose()


def _record(engine, day: date) -> dict:
    done = _done(engine, day)
    todo = [(site, url) for site, url in SITES if site not in done]
    with ThreadPoolExecutor(WORKERS) as pool:
        read = list(pool.map(lambda s: read_site(day, *s), todo))
    rows = [row for got in read for row in got.get("rows", [])]
    if rows:
        _write(engine, rows)
    failed = Counter(got["failed"] for got in read if "failed" in got)
    return {"sites": len(SITES), "already": len(done), "read": len(todo) - sum(failed.values()),
            "links": len(rows), "failed": dict(failed)}


def status(block: dict) -> str:
    """One line for the run's log, numbers only: the Actions log is public."""
    head = "- 大站首页推荐位(影子记录,不进邮件)"
    if block.get("error"):
        return f"{head}:没记录({block['error']})"
    if block.get("skipped"):
        return f"{head}:这轮不记({block.get('why') or '跳过数据库'})"
    if block["already"] == block["sites"]:
        return f"{head}:今天 {block['sites']} 个站都记过了"
    line = f"{head}:读到 {block['read']} 个站,{block['links']} 条链接"
    if block["already"]:
        line += f",另 {block['already']} 个今天已记过"
    failed = "、".join(f"{why} {n} 个" for why, n in sorted(block["failed"].items()))
    return line + (f";没读到:{failed}" if failed else "")
