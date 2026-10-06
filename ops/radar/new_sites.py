"""Radar signal ③b: new sites that already draw search traffic (the "新站主页" step).

A word that catches on gets sites built for it: ai-hailuo.com was registered in August
2026 for the Hailuo video model and ranked for 258 keywords within weeks. DataForSEO's
domain whois overview (via AIsa) finds such domains: registered AND first seen by
DataForSEO within WINDOW_DAYS, with estimated organic traffic over MIN_ETV and at least
MIN_KEYWORDS ranking keywords. Both dates are needed: whois creation dates get rewritten
(dagbladet.no, a 2020 site, showed a July 2026 "created"). The keyword floor drops
gambling and parked domains, which rank for a handful of brand terms.

About $0.13 a query, so the radar runs this once a week (radar.py, Mondays). Each site
is reported once; its name's words go to Jev with the other leads ("hailuo").
"""
from __future__ import annotations

import gzip
import json
import re
from datetime import date, timedelta
from pathlib import Path

import aisa
from terms import STOP

TOOL = "post_dataforseo_domains_whois_overview_live"
WINDOW_DAYS = 90
MIN_ETV = 1000
MIN_KEYWORDS = 20
LIMIT = 30
# domain substring per query; one query each (about $0.13)
QUERIES = {"ai": "%ai%", "video": "%video%"}
DOMAIN_STOP = STOP | {"com", "net", "org", "app", "io", "co", "online", "free", "tool", "tools", "the", "my", "get",
                      "official", "site", "hub", "pro", "best", "video", "videos"}


def name_terms(domain: str) -> list[str]:
    """'ai-hailuo.com' -> ['hailuo']; 'livephoto.video' -> ['livephoto']."""
    label = domain.rsplit(".", 1)[0] if domain.count(".") >= 1 else domain
    words = [w for w in re.split(r"[-_.]+", label.lower()) if w]
    return [w for w in words if w not in DOMAIN_STOP and len(w) >= 4 and not w.isdigit()]


def keep(item: dict) -> bool:
    organic = (item.get("metrics") or {}).get("organic") or {}
    return (organic.get("etv") or 0) > MIN_ETV and (organic.get("count") or 0) >= MIN_KEYWORDS


def site_row(item: dict, query: str) -> dict:
    organic = (item.get("metrics") or {}).get("organic") or {}
    return {"domain": item["domain"], "query": query, "created": str(item.get("created_datetime"))[:10],
            "first_seen": str(item.get("first_seen"))[:10], "etv": int(organic.get("etv") or 0),
            "keywords": int(organic.get("count") or 0)}


def _calls(today: date) -> list[dict]:
    since = (today - timedelta(days=WINDOW_DAYS)).isoformat() + " 00:00:00 +00:00"
    return [{"call_id": name, "tool": TOOL, "arguments": {"body": [{
        "limit": LIMIT, "order_by": ["metrics.organic.etv,desc"],
        "filters": [["created_datetime", ">", since], "and", ["first_seen", ">", since], "and",
                    ["metrics.organic.etv", ">", MIN_ETV], "and", ["domain", "like", pattern]]}]}}
        for name, pattern in QUERIES.items()]


def new_sites(snapshot_dir: Path, today: date | None = None) -> dict:
    today = today or date.today()
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    data, cost = aisa.call_all(_calls(today))
    sites: dict[str, dict] = {}
    for name in QUERIES:
        task = ((data.get(name) or {}).get("tasks") or [{}])[0]
        for item in ((task.get("result") or [{}])[0] or {}).get("items") or []:
            if keep(item) and item["domain"] not in sites:
                sites[item["domain"]] = site_row(item, name)
    path = snapshot_dir / "new_sites.json.gz"
    seen: dict[str, str] = json.loads(gzip.decompress(path.read_bytes())) if path.exists() else {}
    rows = sorted(sites.values(), key=lambda r: -r["etv"])
    for r in rows:
        r["new"] = r["domain"] not in seen
        seen.setdefault(r["domain"], today.isoformat())
    if data:
        path.write_bytes(gzip.compress(json.dumps(seen).encode()))
    terms = [{"term": t, "recent": 1, "note": f"新站 {r['domain']}(注册 {r['created']},约 {r['etv']} 访问/月,{r['keywords']} 个排名词)",
              "examples": [f"{r['domain']} · {r['keywords']} keywords"]}
             for r in rows if r["new"] for t in name_terms(r["domain"])]
    return {"queries": len(QUERIES), "answered": len(data), "cost_micros": cost, "sites": rows, "terms": terms}
