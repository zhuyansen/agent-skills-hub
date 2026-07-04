"""Clarity Data Export API fetcher — aggregated behavior insights for AI.

Token: ops/clarity/.api_token (gitignored) — create at
clarity.microsoft.com → 你的项目 → Settings → Data Export → Generate new API token.

⚠️ API 限制:numOfDays 只能 1-3;每个项目每天最多 10 次请求 —— 省着用,
默认一次拉全维度存盘,分析用本地文件。

Usage:
  python ops/clarity/fetch_clarity.py dump [--days 3]   # 全维度 → ops/clarity/out/*.json
  python ops/clarity/fetch_clarity.py show              # 读本地 dump 摘要(不耗请求数)
"""
import json
import os
import sys

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(HERE, ".api_token")
OUT = os.path.join(HERE, "out")
API = "https://www.clarity.ms/export-data/api/v1/project-live-insights"

DIMENSIONS = ["OS", "Browser", "Device", "Country", "URL", "PageTitle", "ReferrerURL", "Source"]


def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dump"
    if cmd == "show":
        for f in sorted(os.listdir(OUT)) if os.path.isdir(OUT) else []:
            data = json.load(open(os.path.join(OUT, f)))
            print(f"── {f} ──")
            for metric in data[:6]:
                name = metric.get("metricName")
                info = metric.get("information", [])[:5]
                print(f"  {name}: {json.dumps(info, ensure_ascii=False)[:200]}")
        return

    if not os.path.exists(TOKEN_FILE):
        sys.exit("缺少 ops/clarity/.api_token —— clarity.microsoft.com → Settings → Data Export → Generate token,存进该文件")
    token = open(TOKEN_FILE).read().strip()
    days = arg("--days", 3)
    os.makedirs(OUT, exist_ok=True)

    # 一次 dump 用 3 个请求(每天上限 10):无维度总览 + URL 维度 + Source 维度
    for name, dim in [("overview", None), ("by-url", "URL"), ("by-source", "Source")]:
        params = {"numOfDays": days}
        if dim:
            params["dimension1"] = dim
        r = requests.get(API, params=params, headers={"Authorization": f"Bearer {token}"}, timeout=60)
        if r.status_code == 429:
            sys.exit("今日 10 次请求额度用完,明天再拉(或用 show 看本地缓存)")
        r.raise_for_status()
        p = os.path.join(OUT, f"{name}.json")
        json.dump(r.json(), open(p, "w"), ensure_ascii=False, indent=1)
        print(f"  → {p}")
    print("完成(消耗 3/10 每日请求)。指标含:死点击 DeadClick、怒点 RageClick、过度滚动、JS 错误、会话时长等")


if __name__ == "__main__":
    main()
