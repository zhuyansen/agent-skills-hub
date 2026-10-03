"""Radar signal ③: pages competitors and aggregators added since yesterday.

Reads the public sitemaps of five sites (approved 2026-10-03; smithery lists only docs,
so it is left out), keeps yesterday's URLs in a snapshot, and turns today's new URLs
into terms. Only the shards that list tools, servers, skills or posts are read, about 75
requests a day, each site's robots.txt and crawl-delay kept.

LobeHub's index (/sitemap-index.xml) mostly answers 503, its shards do not, so they are
read directly, each as its own source: one shard down does not cost the others. Each
shard is a list of about 200 entries in 17 languages, a featured list rather than the
whole catalog, so a new URL there means "entered LobeHub's list". Locale prefixes are
stripped, or one new entry would count as 17 new URLs.
"""
from __future__ import annotations

import gzip
import json
import re
import time
import urllib.request
from pathlib import Path

from terms import by_source, surges

UA = "Mozilla/5.0 (compatible; agentskillshub-radar/1.0; +https://agentskillshub.top)"
TIMEOUT = 40
RETRIES = 3
RETRY_PAUSE = 10
MIN_URLS = 3
TOP = 25
_LOCALE = r"^(https?://[^/]+)/[a-z]{2}(?:-[A-Za-z]{2,4})?(?=/)"
# site -> (index URL, shard filter or None when the URL is itself a shard,
#          seconds between requests, locale prefix to strip or None)
SOURCES = {
    "glama": ("https://glama.ai/sitemap.xml", r"/(mcp-servers|mcp-remote-servers)/\d+\.xml$|mcp-keyword-reports|blog-posts", 2, None),
    "mcp.so": ("https://mcp.so/sitemap.xml", r"section=(servers|agents|cli|clients|posts)\b", 2, None),
    "skillsmp": ("https://skillsmp.com/sitemap.xml", r"/(skills-discovered|repositories-discovered|skills-popular)\.xml$", 5, None),
    "toolify": ("https://www.toolify.ai/sitemap.xml", r"sitemap_(tools|openclaw_skills)_\d+\.xml$", 2, None),
    **{f"lobehub-{shard}": (f"https://lobehub.com/sitemap/{shard}.xml", None, 5, _LOCALE)
       for shard in ("mcp", "skills", "agents", "blog")},
}
_LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>")


def fetch(url: str) -> str:
    """One sitemap file, three tries. Raises after that: a site with a missing shard is
    skipped for the day, since the URLs it lacks would come back tomorrow as "new"."""
    req = urllib.request.Request(url.replace("&amp;", "&"), headers={"User-Agent": UA})
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
                body = res.read()
            return (gzip.decompress(body) if body[:2] == b"\x1f\x8b" else body).decode("utf-8", "replace")
        except (OSError, ValueError):
            if attempt == RETRIES - 1:
                raise
            time.sleep(RETRY_PAUSE * (attempt + 1))
    return ""


def site_urls(index: str, shard: str | None, pause: float, locale: str | None = None) -> set[str]:
    shards = [index] if shard is None else \
        [u for u in _LOC.findall(fetch(index)) if re.search(shard, u.replace("&amp;", "&"))]
    urls: set[str] = set()
    for i, u in enumerate(shards):
        if i or shard is not None:
            time.sleep(pause)
        urls.update(x.replace("&amp;", "&") for x in _LOC.findall(fetch(u)))
    return {re.sub(locale, r"\1", u) for u in urls} if locale else urls


def slug_text(url: str) -> str:
    """The words a URL carries: its path after the domain, without ids or file suffixes."""
    path = re.sub(r"^https?://[^/]+", "", url).split("?")[0]
    path = re.sub(r"\b[0-9a-f]{8,}\b|\.(html|xml)$", " ", path)
    return re.sub(r"[/_\-]+", " ", path)


def diff(snapshot_dir: Path) -> dict:
    """New URLs per site against the stored snapshot, then the terms that surge in them."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    report, recent, baseline = {}, [], []
    for i, (site, (index, shard, pause, locale)) in enumerate(SOURCES.items()):
        path = snapshot_dir / f"{site}.json.gz"
        old = set(json.loads(gzip.decompress(path.read_bytes()))) if path.exists() else None
        try:
            if i and shard is None:
                time.sleep(pause)   # LobeHub's shards come one after another from one host
            now = site_urls(index, shard, pause, locale)
        except Exception as exc:  # noqa: BLE001 — one site down must not stop the others
            report[site] = {"error": str(exc)[:120]}
            continue
        new = sorted(now - old) if old is not None else []
        report[site] = {"urls": len(now), "new": len(new), "first_run": old is None, "sample": new[:8]}
        recent += [(u, slug_text(u)) for u in new]
        baseline += [(u, slug_text(u)) for u in (old or set())]
        if now:   # an empty answer (blocked, broken) keeps yesterday's snapshot
            path.write_bytes(gzip.compress(json.dumps(sorted(now)).encode()))
    ratio = len(recent) / max(len(baseline), 1)
    return {"sites": report, "terms": surges(by_source(recent), by_source(baseline), ratio, MIN_URLS, TOP)}
