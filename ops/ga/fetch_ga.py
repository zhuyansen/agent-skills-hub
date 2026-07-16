"""Fetch Google Analytics (GA4) data via the Data API REST endpoint.

Standalone (no MCP): uses the same OAuth authorized-user creds as the
analytics-mcp (ops/ga/adc.json — refresh_token based, auto-refreshes).
requests-based transport (AuthorizedSession) honors HTTP(S)_PROXY env vars,
so it works behind the local Clash proxy AND direct on a CI runner.

⚠️ The site's gtag feeds property 485523739 ("新媒体运营"), NOT the empty
"AgentSkillsHub" property (534610783). We query 485523739 and filter
hostName=agentskillshub.top (the property is shared across sites).

Run: python ops/ga/fetch_ga.py [overview|pages|sources|events|dump] [--days 28]
"""
import json
import os
import sys

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request, AuthorizedSession

HERE = os.path.dirname(os.path.abspath(__file__))
ADC = os.path.join(HERE, "adc.json")
OUT = os.path.join(HERE, "out")
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
PROPERTY = os.environ.get("GA_PROPERTY_ID", "485523739")
HOST = "agentskillshub.top"
API = f"https://analyticsdata.googleapis.com/v1beta/properties/{PROPERTY}"

HOST_FILTER = {
    "filter": {
        "fieldName": "hostName",
        "stringFilter": {"matchType": "EXACT", "value": HOST},
    }
}


def session():
    creds = Credentials.from_authorized_user_file(ADC, SCOPES)
    if not creds.valid:
        creds.refresh(Request())
    return AuthorizedSession(creds)


def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


def run_report(sess, dimensions, metrics, days, order_metric=None, limit=25):
    body = {
        "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
        "dimensions": [{"name": d} for d in dimensions],
        "metrics": [{"name": m} for m in metrics],
        "dimensionFilter": HOST_FILTER,
        "limit": limit,
    }
    if order_metric:
        body["orderBys"] = [{"metric": {"metricName": order_metric}, "desc": True}]
    r = sess.post(f"{API}:runReport", json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    dim_n = len(dimensions)
    rows = []
    for row in data.get("rows", []):
        dv = [d["value"] for d in row.get("dimensionValues", [])]
        mv = [m["value"] for m in row.get("metricValues", [])]
        rows.append(
            {**{dimensions[i]: dv[i] for i in range(dim_n)},
             **{metrics[i]: mv[i] for i in range(len(metrics))}}
        )
    return rows


def table(rows, key, cols, top=25):
    if not rows:
        print("  (无数据)")
        return
    for r in rows[:top]:
        vals = "  ".join(f"{c}={r.get(c, '')}" for c in cols)
        print(f"  {str(r.get(key, ''))[:48]:<48} {vals}")


def save(name, data):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"{name}.json")
    with open(p, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"  → {p} ({len(data)} rows)")


PAGE_METRICS = ["screenPageViews", "sessions", "activeUsers", "bounceRate", "userEngagementDuration"]


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "overview"
    days = arg("--days", 28)
    sess = session()
    print(f"GA property {PROPERTY} · host {HOST} · last {days}d\n")

    if cmd in ("overview", "dump"):
        rows = run_report(sess, ["date"], ["sessions", "activeUsers", "screenPageViews",
                          "bounceRate", "userEngagementDuration"], days, limit=400)
        tot_s = sum(int(r["sessions"]) for r in rows)
        tot_u = sum(int(r["activeUsers"]) for r in rows)
        tot_v = sum(int(r["screenPageViews"]) for r in rows)
        print(f"  {days}天: sessions={tot_s} users={tot_u} pageviews={tot_v}")
        save("overview", rows)
    if cmd in ("pages", "dump"):
        print("── 热门页 ──")
        rows = run_report(sess, ["pagePath"], PAGE_METRICS, days, order_metric="screenPageViews", limit=30)
        table(rows, "pagePath", ["screenPageViews", "sessions", "bounceRate"])
        save("pages", rows)
    if cmd in ("sources", "dump"):
        print("── 流量来源 ──")
        rows = run_report(sess, ["sessionSource", "sessionMedium"],
                          ["sessions", "activeUsers"], days, order_metric="sessions", limit=60)
        table(rows, "sessionSource", ["sessionMedium", "sessions"])
        save("sources", rows)
    if cmd in ("events", "dump"):
        print("── 事件/转化 ──")
        rows = run_report(sess, ["eventName"], ["eventCount", "totalUsers"],
                          days, order_metric="eventCount", limit=30)
        table(rows, "eventName", ["eventCount", "totalUsers"])
        save("events", rows)
        # Bot-pollution radar: same events sliced by country. 2026-07-16 lesson —
        # 851 audit_run in one day, 670 from a single Singapore DC scraper; raw
        # counts misled the funnel KPI. Digest uses this to flag concentration.
        geo = run_report(sess, ["eventName", "country"], ["eventCount"],
                         days, order_metric="eventCount", limit=200)
        save("events_geo", geo)


if __name__ == "__main__":
    main()
