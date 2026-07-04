"""Plausible Stats API fetcher — feeds AI analysis.

Key: ops/plausible/.api_key (gitignored) — create at
plausible.io → 头像 → Settings → API Keys → New API Key (type: Stats API).

Usage (any python3, only needs requests):
  python ops/plausible/fetch_plausible.py overview [--days 28]   # 访客/浏览量/跳出/时长
  python ops/plausible/fetch_plausible.py sources  [--days 28]   # utm_source 归因(CLI/MCP 的 utm 在这!)
  python ops/plausible/fetch_plausible.py pages    [--days 28]   # 热门页面
  python ops/plausible/fetch_plausible.py realtime               # 当前在线
  python ops/plausible/fetch_plausible.py dump     [--days 28]   # 全量 → ops/plausible/out/*.json
"""
import json
import os
import sys

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(HERE, ".api_key")
OUT = os.path.join(HERE, "out")
SITE = "agentskillshub.top"
API = "https://plausible.io/api/v2/query"

if not os.path.exists(KEY_FILE):
    sys.exit("缺少 ops/plausible/.api_key —— plausible.io → Settings → API Keys 建一个 Stats API key,内容存进该文件")
KEY = open(KEY_FILE).read().strip()
S = requests.Session()
S.headers["Authorization"] = f"Bearer {KEY}"


def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


def q(metrics, dimensions=None, date_range=None, filters=None, limit=100):
    body = {
        "site_id": SITE,
        "metrics": metrics,
        "date_range": date_range or "28d",
    }
    if dimensions:
        body["dimensions"] = dimensions
    if filters:
        body["filters"] = filters
    body["pagination"] = {"limit": limit}
    r = S.post(API, json=body, timeout=30)
    r.raise_for_status()
    return r.json().get("results", [])


def save(name, data):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"{name}.json")
    json.dump(data, open(p, "w"), ensure_ascii=False, indent=1)
    print(f"  → {p} ({len(data)} rows)")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "overview"
    days = arg("--days", 28)
    rng = f"{days}d"
    M = ["visitors", "pageviews", "bounce_rate", "visit_duration"]

    if cmd == "overview":
        rows = q(M, date_range=rng)
        print(f"{days} 天: visitors={rows[0]['metrics'][0]:,} pageviews={rows[0]['metrics'][1]:,} "
              f"bounce={rows[0]['metrics'][2]}% avg_duration={rows[0]['metrics'][3]}s")
        trend = q(["visitors", "pageviews"], dimensions=["time:day"], date_range=rng, limit=100)
        for r in trend[-7:]:
            print(f"  {r['dimensions'][0]}  visitors={r['metrics'][0]:4} pv={r['metrics'][1]:5}")
    elif cmd == "sources":
        for name, dim in [("SOURCE", "visit:source"), ("UTM_SOURCE", "visit:utm_source")]:
            rows = q(["visitors", "pageviews"], dimensions=[dim], date_range=rng, limit=25)
            print(f"── {name} ──")
            for r in rows[:15]:
                print(f"  {r['metrics'][0]:>6}v {r['metrics'][1]:>7}pv  {r['dimensions'][0]}")
            save(name.lower(), rows)
    elif cmd == "pages":
        rows = q(["visitors", "pageviews", "bounce_rate"], dimensions=["event:page"], date_range=rng, limit=50)
        for r in rows[:20]:
            print(f"  {r['metrics'][0]:>6}v {r['metrics'][1]:>7}pv bounce={r['metrics'][2]}%  {r['dimensions'][0][:60]}")
        save("pages", rows)
    elif cmd == "realtime":
        r = S.get(f"https://plausible.io/api/v1/stats/realtime/visitors?site_id={SITE}", timeout=15)
        print(f"当前在线: {r.text}")
    elif cmd == "dump":
        save("overview", q(M, dimensions=["time:day"], date_range=rng, limit=100))
        save("sources", q(["visitors", "pageviews"], dimensions=["visit:source"], date_range=rng, limit=100))
        save("utm", q(["visitors", "pageviews"], dimensions=["visit:utm_source", "visit:utm_medium"], date_range=rng, limit=100))
        save("pages", q(["visitors", "pageviews", "bounce_rate"], dimensions=["event:page"], date_range=rng, limit=200))
        save("countries", q(["visitors"], dimensions=["visit:country"], date_range=rng, limit=100))
        save("devices", q(["visitors"], dimensions=["visit:device"], date_range=rng))
        print("全量导出 → ops/plausible/out/")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
