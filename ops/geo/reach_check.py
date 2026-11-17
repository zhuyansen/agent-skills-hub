"""Reach-layer check for agentskillshub.top, re-runnable after every deploy and every new
Common Crawl release. Reproduces the 2026-11-16 baseline (出海/精读笔记/hub_reach_check_2026-11-16.md):

  python ops/geo/reach_check.py <report.md> [--crawls 4] [--bing] [--data-dir ops/geo/data]

Checks, all read-only against live site + public Common Crawl index:
  1. gates: robots.txt, llms.txt, llms-full.txt status; homepage under normal + 5 AI-crawler UAs
  2. Common Crawl: latest N crawls, domain match; captures, statuses, /best/ and zh coverage
  3. drift: live sitemap-scenarios /best/ set vs newest crawl's /best/ set (the 2026-11-16
     finding was 14/34 overlap because Aug-Oct retirements + Nov rebuilds postdated the crawl)
  4. --bing: Bing site: spot check for the live /best/ pages missing from the newest crawl

No API keys. CC index 504s are retried once; a crawl that still fails is reported as such,
never as "zero captures". Stdlib only, like ops/seo/page_check.py.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

SITE = "https://agentskillshub.top"
CC_INDEX = "https://index.commoncrawl.org"
UA = "Mozilla/5.0 (compatible; agentskillshub-reachcheck/1.0; +https://agentskillshub.top)"
BOTS = {
    "GPTBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot)",
    "CCBot": "CCBot/2.0 (https://commoncrawl.org/faq/)",
    "ClaudeBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)",
    "PerplexityBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
    "Google-Extended": "Mozilla/5.0 (compatible; Google-Extended/1.0; +http://www.google.com/bot.html)",
}


def fetch(url: str, ua: str = UA, timeout: int = 90, retries: int = 1):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "gzip"})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
                return r.status, raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (502, 503, 504) and attempt < retries:
                time.sleep(6)
                continue
            return e.code, ""
        except Exception:
            if attempt < retries:
                time.sleep(6)
                continue
            return None, ""
    return None, ""


def best_set(urls) -> tuple[set, set]:
    en, zh = set(), set()
    for u in urls:
        u = u.split("?")[0].rstrip("/") + "/"
        if "/best/" not in u:
            continue
        (zh if u.endswith("/zh/") else en).add(u)
    return en, zh


def live_scenario_urls() -> list[str]:
    st, xml = fetch(f"{SITE}/sitemap-scenarios.xml")
    if st != 200:
        return []
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def cc_crawl(cid: str) -> list[dict] | None:
    url = f"{CC_INDEX}/{cid}-index?url=agentskillshub.top&matchType=domain&output=json&limit=3000"
    st, body = fetch(url, retries=2)
    if st != 200:
        return None
    recs = []
    for line in body.splitlines():
        try:
            recs.append(json.loads(line))
        except ValueError:
            pass
    return recs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", type=Path)
    ap.add_argument("--crawls", type=int, default=4)
    ap.add_argument("--bing", action="store_true")
    ap.add_argument("--data-dir", type=Path, default=Path(__file__).parent / "data")
    args = ap.parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"# Reach check — {SITE}", f"date: {time.strftime('%Y-%m-%d')}", ""]

    # 1. gates
    lines += ["## Gates", ""]
    for path in ("/robots.txt", "/llms.txt", "/llms-full.txt"):
        st, body = fetch(SITE + path)
        lines.append(f"- `{path}` → {st}, {len(body.encode())} bytes")
    st, home = fetch(SITE + "/")
    sizes = {}
    for name, ua in [("normal", UA), *BOTS.items()]:
        s, b = fetch(SITE + "/", ua=ua)
        sizes[name] = (s, len(b.encode()))
        time.sleep(0.3)
    uniform = len({v for v in sizes.values()}) == 1
    lines.append(f"- homepage UA matrix: {sizes}")
    lines.append(f"- UA discrimination: {'NONE (pass)' if uniform else 'PRESENT (fail)'}")
    lines.append("")

    # 2. Common Crawl
    st, body = fetch(f"{CC_INDEX}/collinfo.json")
    crawls = [c["id"] for c in json.loads(body)[: args.crawls]] if st == 200 else []
    lines += ["## Common Crawl", ""]
    newest_best_en: set = set()
    newest_best_zh: set = set()
    for i, cid in enumerate(crawls):
        recs = cc_crawl(cid)
        if recs is None:
            lines.append(f"- {cid}: INDEX ERROR (504/timeout) — not zero captures")
            continue
        (args.data_dir / f"cc_{cid}.json").write_text(json.dumps(recs))
        statuses = Counter(r.get("status", "?") for r in recs)
        en, zh = best_set(r.get("url", "") for r in recs if r.get("status") == "200")
        if i == 0:
            newest_best_en, newest_best_zh = en, zh
        lines.append(f"- {cid}: {len(recs)} captures, statuses={dict(statuses)}, /best/ en={len(en)} zh={len(zh)}")
        time.sleep(2)
    lines.append("")

    # 3. drift vs live sitemap
    live_en, live_zh = best_set(live_scenario_urls())
    lines += ["## Drift: live sitemap vs newest crawl", ""]
    if newest_best_en or newest_best_zh:
        missing = sorted(live_en - newest_best_en)
        stale = sorted(newest_best_en - live_en)
        lines.append(f"- live /best/: {len(live_en)} en + {len(live_zh)} zh")
        lines.append(f"- overlap en: {len(live_en & newest_best_en)}/{len(live_en)}; zh in crawl: {len(newest_best_zh)}/{len(live_zh)}")
        lines.append(f"- live en missing from crawl ({len(missing)}): {[u.replace(SITE, '') for u in missing]}")
        lines.append(f"- crawl en retired/absent from sitemap ({len(stale)}): {[u.replace(SITE, '') for u in stale]}")
    else:
        lines.append("- newest crawl unavailable; drift not computed")
    lines.append("")

    # 4. Bing spot check
    if args.bing and newest_best_en:
        lines += ["## Bing site: spot check (live en missing from newest crawl)", ""]
        for u in sorted(live_en - newest_best_en):
            q = urllib.parse.quote("site:" + u.replace(SITE, ""))
            st, html = fetch(f"https://www.bing.com/search?q={q}&count=10",
                             ua="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36")
            path = u.replace(SITE, "")
            if st == 200 and 'class="b_algo"' in html and path in html:
                verdict = "INDEXED"
            elif st == 200:
                verdict = "NOT INDEXED / unknown"
            else:
                verdict = f"HTTP {st}"
            lines.append(f"- `{path}` → {verdict}")
            time.sleep(1.2)
        lines.append("")

    args.report.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nreport → {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
