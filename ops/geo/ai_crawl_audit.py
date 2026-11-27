#!/usr/bin/env python3
"""Lightweight GEOInflow-style AI Crawler & Sitemap Blind-Spot Auditor for agentskillshub.top.

Reads deduplicated edge telemetry from Cloudflare Workers KV (`ash-ai-crawl-log`)
and reconciles observed AI crawler visits against live sitemap.xml to surface:
  1. Crawler hits by bot, provider, purpose (training vs ai_search vs user_triggered) & IP verification
  2. AI referral landing pages (ChatGPT / Perplexity / Claude / Gemini / etc.)
  3. Sitemap blind spots: core pages (/best/*, /how-we-grade/, /ai-info/) with ZERO AI crawls

Usage:
  python3 ops/geo/ai_crawl_audit.py
  python3 ops/geo/ai_crawl_audit.py --days 14 --no-save
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ACCOUNT_ID = "111392dcb718001bfa28a9ef3b17f804"
AE_DATASET = "ash_ai_crawl_log"
KV_NAMESPACE_ID = "129a42bc278d452cb8f950b8e8acf1af"  # legacy read-only fallback
SITE = "https://agentskillshub.top"
UA = "AgentSkillsHub-CrawlAudit/1.0 (+https://agentskillshub.top/ai-info/)"
PANEL_DIR = Path(__file__).resolve().parent / "panel"


def get_cf_token() -> str:
    env_tok = os.environ.get("CLOUDFLARE_API_TOKEN")
    if env_tok:
        return env_tok
    cfg_path = Path.home() / "Library/Preferences/.wrangler/config/default.toml"
    if cfg_path.exists():
        m = re.search(r'oauth_token\s*=\s*"([^"]+)"', cfg_path.read_text("utf-8", "ignore"))
        if m:
            return m.group(1)
    raise RuntimeError("No Cloudflare token found. Run `npx wrangler login` or set CLOUDFLARE_API_TOKEN.")


def cf_get_json(url: str, token: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            subprocess.run(
                ["npx", "--yes", "wrangler", "whoami"],
                env={**os.environ, "NPM_CONFIG_CACHE": "/tmp/npm-wrangler-cache"},
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            fresh = get_cf_token()
            req2 = urllib.request.Request(url, headers={"Authorization": f"Bearer {fresh}", "User-Agent": UA})
            with urllib.request.urlopen(req2, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8", "ignore"))
        raise


def query_ae_sql(token: str, days: int) -> list[dict[str, Any]]:
    sql = (
        "SELECT "
        "toDate(timestamp) AS day, "
        "blob1 AS kind, "
        "blob2 AS actor, "
        "blob3 AS path, "
        "blob6 AS ip_status, "
        "SUM(_sample_interval) AS hits "
        f"FROM {AE_DATASET} "
        f"WHERE timestamp >= NOW() - INTERVAL '{int(days)}' DAY "
        "GROUP BY day, kind, actor, path, ip_status "
        "FORMAT JSON"
    )
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/analytics_engine/sql"
    req = urllib.request.Request(
        url,
        data=sql.encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "User-Agent": UA},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8", "ignore"))
    return payload.get("data", [])


def list_kv_keys(token: str, prefix: str = "") -> list[str]:
    keys: list[str] = []
    cursor = ""
    while True:
        params = {"limit": "1000"}
        if prefix:
            params["prefix"] = prefix
        if cursor:
            params["cursor"] = cursor
        qs = urllib.parse.urlencode(params)
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/storage/kv/namespaces/{KV_NAMESPACE_ID}/keys?{qs}"
        data = cf_get_json(url, token)
        for item in data.get("result", []):
            keys.append(item["name"])
        cursor = (data.get("result_info") or {}).get("cursor") or ""
        if not cursor:
            break
    return keys


def read_kv_value(token: str, key: str) -> dict[str, Any] | None:
    enc = urllib.parse.quote(key, safe="")
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/storage/kv/namespaces/{KV_NAMESPACE_ID}/values/{enc}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8", "ignore"))
    except Exception:
        return None


def fetch_sitemap_paths() -> list[str]:
    paths: set[str] = set()

    def _parse(url: str, depth: int = 0) -> None:
        if depth > 2:
            return
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            xml_bytes = urllib.request.urlopen(req, timeout=15).read()
            root = ET.fromstring(xml_bytes)
        except Exception:
            return
        tag = root.tag.lower()
        if tag.endswith("sitemapindex"):
            for loc in root.iter():
                if loc.tag.lower().endswith("loc") and loc.text:
                    sub = loc.text.strip()
                    if any(k in sub for k in ("sitemap-static", "sitemap-scenarios", "sitemap-core", "sitemap-best", "sitemap-pages")):
                        _parse(sub, depth + 1)
        else:
            for loc in root.iter():
                if loc.tag.lower().endswith("loc") and loc.text:
                    parsed = urllib.parse.urlparse(loc.text.strip())
                    paths.add(parsed.path or "/")

    _parse(f"{SITE}/sitemap.xml")
    return sorted(paths)


def is_monitored_core_path(path: str) -> bool:
    return (
        path == "/"
        or path.startswith("/best/")
        or path.startswith("/how-we-grade")
        or path.startswith("/ai-info")
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Cloudflare AI crawler logs & Sitemap blind spots")
    ap.add_argument("--days", type=int, default=30, help="Lookback window in days (default: 30)")
    ap.add_argument("--source", choices=("auto", "ae", "kv"), default="auto", help="Telemetry backend: ae (Analytics Engine), kv (legacy), or auto")
    ap.add_argument("--fetch-values", action="store_true", help="Legacy KV mode: fetch per-key JSON values for IP verification breakdown")
    ap.add_argument("--no-save", action="store_true", help="Do not save JSON snapshot")
    args = ap.parse_args()

    token = get_cf_token()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime("%Y-%m-%d")

    bot_counts: Counter[str] = Counter()
    bot_hits: Counter[str] = Counter()
    path_bots: dict[str, set[str]] = defaultdict(set)
    ip_status_counts: Counter[str] = Counter()
    ref_counts: Counter[str] = Counter()
    ref_paths: Counter[str] = Counter()
    source_used = args.source

    ae_rows: list[dict[str, Any]] | None = None
    if args.source in ("auto", "ae"):
        try:
            ae_rows = query_ae_sql(token, args.days)
            source_used = "analytics_engine"
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")[:200]
            if args.source == "ae":
                raise RuntimeError(
                    f"Analytics Engine SQL query failed (HTTP {e.code}): {body}. "
                    "Ensure CLOUDFLARE_API_TOKEN has 'Account Analytics: Read' permission."
                ) from e
            print(f"[warn] Analytics Engine SQL unavailable (HTTP {e.code}); falling back to legacy KV. Set CLOUDFLARE_API_TOKEN with Account Analytics:Read for AE queries.")
            ae_rows = None

    if ae_rows is not None:
        seen_day_bot_path: set[tuple[str, str, str]] = set()
        seen_day_ref_path: set[tuple[str, str, str]] = set()
        for row in ae_rows:
            day = str(row.get("day") or "")
            kind = str(row.get("kind") or "")
            actor = str(row.get("actor") or "")
            path = str(row.get("path") or "/")
            ip_status = str(row.get("ip_status") or "")
            hits = int(round(float(row.get("hits") or 1)))
            if day < cutoff:
                continue
            if kind == "crawl":
                key3 = (day, actor, path)
                if key3 not in seen_day_bot_path:
                    seen_day_bot_path.add(key3)
                    bot_counts[actor] += 1
                bot_hits[actor] += hits
                path_bots[path].add(actor)
                if ip_status:
                    ip_status_counts[f"{actor}:{ip_status}"] += hits
            elif kind == "ref":
                key3 = (day, actor, path)
                if key3 not in seen_day_ref_path:
                    seen_day_ref_path.add(key3)
                    ref_counts[actor] += 1
                ref_paths[f"{actor} -> {path}"] += hits
    else:
        source_used = "kv_legacy"
        crawl_keys = list_kv_keys(token, prefix="crawl|")
        ref_keys = list_kv_keys(token, prefix="ref|")

        for k in crawl_keys:
            parts = k.split("|", 3)
            if len(parts) != 4:
                continue
            _, day, bot, path = parts
            if day < cutoff:
                continue
            bot_counts[bot] += 1
            path_bots[path].add(bot)
            if args.fetch_values:
                val = read_kv_value(token, k)
                if val:
                    ip_status_counts[f"{bot}:{val.get('ip_status', 'unknown')}"] += 1

        for k in ref_keys:
            parts = k.split("|", 3)
            if len(parts) != 4:
                continue
            _, day, engine, path = parts
            if day < cutoff:
                continue
            ref_counts[engine] += 1
            ref_paths[f"{engine} -> {path}"] += 1

    sitemap_paths = fetch_sitemap_paths()
    core_paths = [p for p in sitemap_paths if is_monitored_core_path(p)]
    crawled_core = [p for p in core_paths if p in path_bots]
    blind_spots = [p for p in core_paths if p not in path_bots]

    report = {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source_used,
        "window_days": args.days,
        "cutoff_day": cutoff,
        "total_crawl_day_records": sum(bot_counts.values()),
        "total_crawl_hits": sum(bot_hits.values()) if bot_hits else sum(bot_counts.values()),
        "unique_crawled_paths": len(path_bots),
        "bots": dict(bot_counts.most_common()),
        "bot_hits": dict(bot_hits.most_common()),
        "ip_verification": dict(ip_status_counts.most_common()),
        "ai_referrals": dict(ref_counts.most_common()),
        "ai_referral_top_landings": dict(ref_paths.most_common(20)),
        "sitemap_core_total": len(core_paths),
        "sitemap_core_crawled": len(crawled_core),
        "sitemap_core_coverage_pct": round(100.0 * len(crawled_core) / max(1, len(core_paths)), 1),
        "blind_spots_sample": blind_spots[:30],
    }

    print("=== AgentSkillsHub AI Crawler & Sitemap Coverage Audit ===")
    print(
        f"Source: {source_used} | Window: last {args.days}d (since {cutoff}) | "
        f"Bot day-path records: {report['total_crawl_day_records']} | "
        f"Total hits: {report['total_crawl_hits']} | Unique paths: {report['unique_crawled_paths']}"
    )
    print("Bots (day-path):", report["bots"] or "(none yet — telemetry just activated)")
    if report["bot_hits"]:
        print("Bots (raw hits):", report["bot_hits"])
    if report["ip_verification"]:
        print("IP Verification:", report["ip_verification"])
    print("AI Referrals:", report["ai_referrals"] or "(none yet)")
    print(
        f"Core Sitemap Coverage (/ + /best/* + /how-we-grade + /ai-info): "
        f"{report['sitemap_core_crawled']}/{report['sitemap_core_total']} ({report['sitemap_core_coverage_pct']}%)"
    )
    if blind_spots:
        print(f"Sample Blind Spots (first 10 of {len(blind_spots)}):")
        for p in blind_spots[:10]:
            print(f"  - {p}")

    if not args.no_save:
        PANEL_DIR.mkdir(parents=True, exist_ok=True)
        out = PANEL_DIR / f"ai-crawl-audit-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
