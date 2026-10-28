"""Index watch: which of our pages Google has indexed, and how long that took.

Each day, for each site: read its sitemaps and note the day a URL first shows up there; count a
page with impressions in the last 28 days as indexed without asking; spend the URL Inspection
quota on the rest, new pages first. Results go to index_pages and index_checks
(supabase/migrations/031_index_watch.sql). The log prints counts only: this repository's
Actions logs are public.

  python ops/index/index_watch.py [--dry-run] [--limit N]   # every site; --dry-run writes nothing
  python ops/index/index_watch.py report                    # per site and kind, from the tables

Needs ops/gsc/token.json (webmasters.readonly is enough) and SUPABASE_DB_URL. Shadow mode from
2026-10-28 for two weeks: it records and alerts nobody.
"""
from __future__ import annotations

import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import astuple, dataclass
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops/gsc"))
import fetch_gsc as gsc  # noqa: E402

SITES = {  # Search Console property → its sitemap
    "sc-domain:agentskillshub.top": "https://agentskillshub.top/sitemap.xml",
    "sc-domain:jasonzhu.ai": "https://jasonzhu.ai/sitemap.xml",
}
# more sites, from a secret, never named in this public repo or its logs:
# {"<property>": {"sitemap": "<url>", "since": "<launch day, YYYY-MM-DD>"}}
EXTRA_SITES = "INDEX_WATCH_EXTRA_SITES"
INSPECT = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
DAILY_BUDGET = 1800        # inspections per property a day: the quota is 2,000, the rest is for checks by hand
PAUSE = 0.12               # seconds between inspections: the quota is 600 a minute
SEARCH_DAYS = 28           # impressions in this window count as indexed
SEARCH_ROWS = 25000        # the most rows one Search Analytics call returns
NEW_DAYS = 30              # a page this young is inspected every day until it is indexed
UNINDEXED_EVERY = 7        # days between inspections of an older page that is not indexed
INDEXED_EVERY = 30         # days between inspections of an indexed page without impressions
SAVE_EVERY = 200           # inspections written per transaction
TIMEOUT = 60               # seconds for each HTTP call
CONNECT_TIMEOUT = 30       # seconds to reach the database
QUOTA_HIT = 429
INDEXED = ("Submitted and indexed", "Indexed, not submitted in sitemap")
LOCALES = {"zh", "en", "ja", "ko"}
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
UA = {"User-Agent": "index-watch (+https://agentskillshub.top)"}
FIELDS = {  # index_checks column → indexStatusResult key
    "verdict": "verdict", "coverage_state": "coverageState", "indexing_state": "indexingState",
    "page_fetch_state": "pageFetchState", "robots_state": "robotsTxtState", "last_crawl": "lastCrawlTime",
    "google_canonical": "googleCanonical", "user_canonical": "userCanonical", "sitemaps": "sitemap",
}


@dataclass
class Page:
    """One row of index_pages; the field order is the column order."""
    url: str
    site: str
    kind: str
    first_seen: date | None = None      # the first day our sitemaps listed it; None: before the watch began
    lastmod: date | None = None
    in_sitemap: bool = True
    search_seen: date | None = None     # the last day a 28-day read had impressions for it
    last_checked: date | None = None
    last_state: str | None = None       # coverageState of the last inspection
    first_indexed: date | None = None


class Quota(Exception):
    """The property's inspections for today are spent."""


COLUMNS = tuple(Page.__dataclass_fields__)


# --- sitemaps ---------------------------------------------------------------------------

def kind(url: str) -> str:
    """The first path segment after a locale: skill, best, blog, prompts ...; home for the root."""
    parts = [p for p in urlsplit(url).path.split("/") if p]
    if parts and parts[0].lower() in LOCALES:
        parts = parts[1:]
    return parts[0].lower() if parts else "home"


def day(text: str | None) -> date | None:
    try:
        return date.fromisoformat((text or "").strip()[:10])
    except ValueError:
        return None


def fetch(url: str) -> bytes:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.content


def entries(xml: bytes) -> dict[str, date | None]:
    """A urlset's URLs with their lastmod."""
    urls = ET.fromstring(xml).findall("s:url", NS)
    return {u.findtext("s:loc", "", NS).strip(): day(u.findtext("s:lastmod", None, NS)) for u in urls}


def sitemap(root: str, get=fetch) -> dict[str, date | None]:
    """Every URL under the sitemap at root, through one level of sitemap index."""
    xml = get(root)
    kids = [s.findtext("s:loc", "", NS).strip() for s in ET.fromstring(xml).findall("s:sitemap", NS)]
    if not kids:
        return entries(xml)
    listed = {}
    for kid in kids:
        listed.update(entries(get(kid)))
    return listed


def merge(pages: dict[str, Page], listed: dict, site: str, today: date, since: date | None = None) -> dict[str, Page]:
    """The pages plus what the sitemaps list today. On a site's first run every listed URL predates the
    watch, unless the site's launch day is known: then that is the day they appeared."""
    first_run = not pages
    for url, lastmod in listed.items():
        page = pages.get(url) or Page(url, site, kind(url), first_seen=since if first_run else today)
        page.lastmod, page.in_sitemap = lastmod, True
        pages[url] = page
    for url in pages.keys() - listed.keys():
        pages[url].in_sitemap = False
    return pages


# --- what to inspect --------------------------------------------------------------------

def recent(when: date | None, today: date, days: int) -> bool:
    return when is not None and (today - when).days < days


def note_search(pages: dict[str, Page], seen: set[str], today: date) -> None:
    """Pages with impressions are indexed: no inspection needed while that lasts."""
    for url in seen & pages.keys():
        pages[url].search_seen = today
        pages[url].first_indexed = pages[url].first_indexed or today


def due(page: Page, today: date) -> int | None:
    """How urgent an inspection is today, lowest first, or None when it is not due."""
    if not page.in_sitemap or page.last_checked == today or recent(page.search_seen, today, SEARCH_DAYS):
        return None
    indexed = page.last_state in INDEXED
    if page.first_seen and not indexed and recent(page.first_seen, today, NEW_DAYS):
        return 0
    if page.last_checked is None:
        return 1
    if not indexed and not recent(page.last_checked, today, UNINDEXED_EVERY):
        return 2
    if indexed and not recent(page.last_checked, today, INDEXED_EVERY):
        return 3
    return None


def pick(pages, today: date, limit: int) -> list[Page]:
    """The pages to inspect today, most urgent first, the longest unchecked first within each."""
    ranked = [(due(p, today), p.last_checked or date.min, p.url, p) for p in pages]
    return [row[-1] for row in sorted(r for r in ranked if r[0] is not None)[:limit]]


# --- Search Console ---------------------------------------------------------------------

def searched(sess, site: str, today: date) -> set[str]:
    """Pages with impressions in the last SEARCH_DAYS days, the not yet final days included."""
    start = today - timedelta(days=SEARCH_DAYS)
    rows = gsc.query(sess, site, start, today, ["page"], limit=SEARCH_ROWS, data_state="all")
    return {r["page"] for r in rows}


def inspect(sess, site: str, url: str) -> dict | None:
    """One URL's indexStatusResult, or None when the call failed. Raises Quota at the daily limit."""
    try:
        r = sess.post(INSPECT, json={"inspectionUrl": url, "siteUrl": site}, timeout=TIMEOUT)
    except requests.RequestException:
        return None
    if r.status_code == QUOTA_HIT:
        raise Quota(site)
    if not r.ok:
        return None
    return r.json().get("inspectionResult", {}).get("indexStatusResult", {})


def apply(page: Page, status: dict, today: date) -> dict:
    """Note an inspection on its page and return its index_checks row."""
    page.last_checked, page.last_state = today, status.get("coverageState")
    if page.last_state in INDEXED and not page.first_indexed:
        page.first_indexed = today
    return {"url": page.url, **{col: status.get(key) for col, key in FIELDS.items()}}


def inspect_chunk(sess, site: str, chunk: list[Page], today: date, tally: Counter) -> list[dict]:
    checks = []
    for page in chunk:
        status = inspect(sess, site, page.url)
        time.sleep(PAUSE)
        if status is None:
            tally["failed"] += 1
            continue
        checks.append(apply(page, status, today))
        tally[page.last_state or "no state"] += 1
    return checks


# --- the tables -------------------------------------------------------------------------

UPSERT = (f"INSERT INTO index_pages ({', '.join(COLUMNS)}) VALUES %s ON CONFLICT (url) DO UPDATE SET "
          + ", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS[1:]))
CHECK_COLUMNS = ("url", *FIELDS)


def connect():
    import psycopg2
    return psycopg2.connect(os.environ["SUPABASE_DB_URL"], connect_timeout=CONNECT_TIMEOUT)


def run(conn, sql: str, rows=None, params=None):
    """One transaction with its own statement timeout (the pooler is in transaction mode).
    rows: many value tuples for a VALUES %s statement; otherwise the fetched rows, if any."""
    from psycopg2.extras import execute_values
    with conn, conn.cursor() as cur:
        cur.execute("SET LOCAL statement_timeout = '60s'")
        if rows is not None:
            return execute_values(cur, sql, rows)
        cur.execute(sql, params)
        return cur.fetchall() if cur.description else None


def load(conn, site: str) -> dict[str, Page]:
    if conn is None:
        return {}
    rows = run(conn, f"SELECT {', '.join(COLUMNS)} FROM index_pages WHERE site = %(site)s", params={"site": site})
    return {row[0]: Page(*row) for row in rows}


def save(conn, pages, checks: list[dict]) -> None:
    if conn is None:
        return
    run(conn, UPSERT, [astuple(p) for p in pages])
    if checks:
        sql = f"INSERT INTO index_checks ({', '.join(CHECK_COLUMNS)}) VALUES %s"
        run(conn, sql, [tuple(c[k] for k in CHECK_COLUMNS) for c in checks])


# --- a run ------------------------------------------------------------------------------

def watch(sess, conn, site: str, root: str, today: date, limit: int, since: date | None = None) -> Counter:
    pages = merge(load(conn, site), sitemap(root), site, today, since)
    seen = searched(sess, site, today)
    note_search(pages, seen, today)
    save(conn, pages.values(), [])
    todo = pick(pages.values(), today, limit)
    tally = Counter(listed=sum(p.in_sitemap for p in pages.values()), searched=len(seen & pages.keys()),
                    new=sum(p.first_seen == today for p in pages.values()), due=len(todo))
    try:
        for start in range(0, len(todo), SAVE_EVERY):
            chunk = todo[start:start + SAVE_EVERY]
            save(conn, chunk, inspect_chunk(sess, site, chunk, today, tally))
    except Quota:
        tally["quota spent"] += 1
    return tally


def line(site: str, tally: Counter) -> str:
    head = ("listed", "new", "searched", "due", "failed", "quota spent")
    states = ", ".join(f"{k} {v}" for k, v in tally.most_common() if k not in head)
    return f"{site}: " + ", ".join(f"{k} {tally[k]}" for k in head) + (f" | {states}" if states else "")


REPORT = """
SELECT site, kind, count(*) AS pages,
       count(*) FILTER (WHERE last_state IN %(indexed)s OR search_seen >= current_date - %(days)s) AS indexed,
       count(*) FILTER (WHERE first_seen IS NOT NULL) AS new_pages,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY first_indexed - first_seen) AS median_days_to_index
FROM index_pages WHERE in_sitemap GROUP BY site, kind ORDER BY site, pages DESC
"""
STATES = """
SELECT site, coalesce(last_state, 'not inspected'), count(*) FROM index_pages
WHERE in_sitemap AND NOT coalesce(search_seen >= current_date - %(days)s, false) GROUP BY 1, 2 ORDER BY 1, 3 DESC
"""


def report(conn) -> None:
    """Per site and kind: pages, indexed, new since the watch began, median days to index; then where the rest stand."""
    for sql in (REPORT, STATES):
        rows = run(conn, sql, params={"indexed": INDEXED, "days": SEARCH_DAYS})
        print("\n".join(" | ".join(str(v) for v in row) for row in rows), end="\n\n")


def sites(env: dict | None = None) -> list[tuple[str, str, date | None, str]]:
    """(property, sitemap, launch day, the name the log prints): a site from the secret prints as "extra site N"."""
    out = [(site, root, None, site) for site, root in SITES.items()]
    extra = json.loads((os.environ if env is None else env).get(EXTRA_SITES) or "{}")
    for n, (site, conf) in enumerate(sorted(extra.items()), 1):
        since = date.fromisoformat(conf["since"]) if conf.get("since") else None
        out.append((site, conf["sitemap"], since, f"extra site {n}"))
    return out


def main(argv: list[str]) -> None:
    if argv[:1] == ["report"]:
        return report(connect())
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else DAILY_BUDGET
    conn = None if "--dry-run" in argv else connect()
    sess, today, failed = gsc.get_service(), date.today(), []
    for site, root, since, name in sites():
        try:
            print(line(name, watch(sess, conn, site, root, today, limit, since)), flush=True)
        except Exception as e:  # noqa: BLE001 - a secret site's traceback would print its address
            if name == site:
                raise
            failed.append(name)
            print(f"{name}: failed ({type(e).__name__})", flush=True)
    if failed:
        sys.exit(f"failed: {', '.join(failed)}")


if __name__ == "__main__":
    main(sys.argv[1:])
