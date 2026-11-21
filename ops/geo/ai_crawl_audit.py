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
KV_NAMESPACE_ID = "129a42bc278d452cb8f950b8e8acf1af"
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
    ap.add_argument("--fetch-values", action="store_true", help="Fetch per-key JSON values (for IP verification breakdown)")
    ap.add_argument("--no-save", action="store_true", help="Do not save JSON snapshot")
    args = ap.parse_args()

    token = get_cf_token()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime("%Y-%m-%d")

    crawl_keys = list_kv_keys(token, prefix="crawl|")
    ref_keys = list_kv_keys(token, prefix="ref|")

    bot_counts: Counter[str] = Counter()
    path_bots: dict[str, set[str]] = defaultdict(set)
    ip_status_counts: Counter[str] = Counter()
    ref_counts: Counter[str] = Counter()
    ref_paths: Counter[str] = Counter()

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
        "window_days": args.days,
        "cutoff_day": cutoff,
        "total_crawl_day_records": sum(bot_counts.values()),
        "unique_crawled_paths": len(path_bots),
        "bots": dict(bot_counts.most_common()),
        "ip_verification": dict(ip_status_counts.most_common()),
        "ai_referrals": dict(ref_counts.most_common()),
        "ai_referral_top_landings": dict(ref_paths.most_common(20)),
        "sitemap_core_total": len(core_paths),
        "sitemap_core_crawled": len(crawled_core),
        "sitemap_core_coverage_pct": round(100.0 * len(crawled_core) / max(1, len(core_paths)), 1),
        "blind_spots_sample": blind_spots[:30],
    }

    print("=== AgentSkillsHub AI Crawler & Sitemap Coverage Audit ===")
    print(f"Window: last {args.days}d (since {cutoff}) | Bot day-path records: {report['total_crawl_day_records']} | Unique paths: {report['unique_crawled_paths']}")
    print("Bots:", report["bots"] or "(none yet — telemetry just activated)")
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
