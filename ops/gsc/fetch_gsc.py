"""GSC data fetcher for agentskillshub.top — feeds AI analysis.

Auth: OAuth desktop flow. First run opens a browser for consent, then caches
ops/gsc/token.json (both credential files are gitignored).

Usage (from backend venv):
  python ops/gsc/fetch_gsc.py sites                       # list verified properties
  python ops/gsc/fetch_gsc.py queries [--days 28]         # top queries
  python ops/gsc/fetch_gsc.py pages   [--days 28]         # top pages
  python ops/gsc/fetch_gsc.py page-queries <url-substr>   # queries hitting one page
  python ops/gsc/fetch_gsc.py compare [--days 28]         # this period vs previous
  python ops/gsc/fetch_gsc.py dump    [--days 28]         # everything → ops/gsc/out/*.json

Output goes to stdout as aligned tables AND ops/gsc/out/*.json for AI analysis.
"""
import json
import os
import sys
from datetime import date, timedelta

from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# requests-based transport (NOT googleapiclient/httplib2): httplib2 ignores
# HTTP(S)_PROXY env vars, which times out behind the local Clash proxy.
# requests honors them. REST endpoints are simple enough to call directly.
API = "https://www.googleapis.com/webmasters/v3"

HERE = os.path.dirname(os.path.abspath(__file__))
CREDS = os.path.join(HERE, "credentials.json")
TOKEN = os.path.join(HERE, "token.json")
OUT = os.path.join(HERE, "out")
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
# sc-domain covers the whole domain (all subdomains/protocols); fall back to
# the URL-prefix property if that's how the site was verified.
SITE_CANDIDATES = ["sc-domain:agentskillshub.top", "https://agentskillshub.top/"]

ROW_LIMIT = 500


def get_service():
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS):
                sys.exit(
                    f"缺少 {CREDS}\n"
                    "→ Google Cloud Console 创建 OAuth 桌面客户端并下载 JSON,"
                    "重命名为 credentials.json 放到 ops/gsc/ 下。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, "w") as f:
            f.write(creds.to_json())
    return AuthorizedSession(creds)


def api_get(sess, path):
    r = sess.get(f"{API}{path}", timeout=30)
    r.raise_for_status()
    return r.json()


def api_post(sess, path, body):
    r = sess.post(f"{API}{path}", json=body, timeout=60)
    r.raise_for_status()
    return r.json()


def list_sites(sess):
    return api_get(sess, "/sites").get("siteEntry", [])


def pick_site(sess):
    mine = {s["siteUrl"] for s in list_sites(sess)}
    for cand in SITE_CANDIDATES:
        if cand in mine:
            return cand
    sys.exit(f"账号下没有匹配的 property。可用: {sorted(mine)}")


def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


def query(svc, site, start, end, dimensions, filters=None, limit=ROW_LIMIT):
    from urllib.parse import quote
    body = {
        "startDate": str(start),
        "endDate": str(end),
        "dimensions": dimensions,
        "rowLimit": limit,
    }
    if filters:
        body["dimensionFilterGroups"] = [{"filters": filters}]
    rows = api_post(svc, f"/sites/{quote(site, safe='')}/searchAnalytics/query", body).get("rows", [])
    return [
        {
            **{d: r["keys"][i] for i, d in enumerate(dimensions)},
            "clicks": r["clicks"],
            "impressions": r["impressions"],
            "ctr": round(r["ctr"] * 100, 2),
            "position": round(r["position"], 1),
        }
        for r in rows
    ]


def table(rows, key, top=25):
    if not rows:
        print("  (无数据)")
        return
    w = max(len(str(r[key])[:70]) for r in rows[:top])
    print(f"  {'#':<3} {key:<{w}} {'clicks':>7} {'impr':>8} {'ctr%':>6} {'pos':>6}")
    for i, r in enumerate(rows[:top], 1):
        print(f"  {i:<3} {str(r[key])[:70]:<{w}} {r['clicks']:>7} {r['impressions']:>8} {r['ctr']:>6} {r['position']:>6}")


def save(name, data):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"{name}.json")
    with open(p, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"  → {p} ({len(data)} rows)")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "queries"
    days = arg("--days", 28)
    end = date.today() - timedelta(days=2)  # GSC data lags ~2 days
    start = end - timedelta(days=days - 1)

    svc = get_service()
    if cmd == "sites":
        for s in list_sites(svc):
            print(f"  {s['siteUrl']}  ({s['permissionLevel']})")
        return
    site = pick_site(svc)
    print(f"property: {site} · {start} → {end}\n")

    if cmd == "queries":
        rows = query(svc, site, start, end, ["query"])
        table(rows, "query")
        save("queries", rows)
    elif cmd == "brand":
        # Brand-word monitor: are we #1 for our own name? Watch as awareness
        # grows (the copycat agentskillshub.dev + our github repo outrank the
        # spaced generic phrase "agent skills hub"; the one-word form is fine).
        terms = ["agent skills hub", "agent skill hub", "agentskillshub",
                 "agent-skills-hub", "skills hub", "claude skills hub"]
        rows = [r for r in query(svc, site, start, end, ["query"], limit=1000)
                if any(t in r["query"].lower() for t in terms)]
        rows.sort(key=lambda r: -r["impressions"])
        table(rows, "query", top=40)
        ti = sum(r["impressions"] for r in rows) or 1
        tc = sum(r["clicks"] for r in rows)
        print(f"\n  brand family: {ti} impr, {tc} clicks, CTR {tc / ti * 100:.1f}% "
              f"— aim: exact-name queries at pos 1")
        save("brand", rows)
    elif cmd == "pages":
        rows = query(svc, site, start, end, ["page"])
        table(rows, "page")
        save("pages", rows)
    elif cmd == "page-queries":
        target = sys.argv[2]
        rows = query(svc, site, start, end, ["query"], filters=[
            {"dimension": "page", "operator": "contains", "expression": target}
        ])
        table(rows, "query")
        save(f"page-queries-{target.strip('/').replace('/', '_')[:40]}", rows)
    elif cmd == "compare":
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)
        cur = {r["query"]: r for r in query(svc, site, start, end, ["query"])}
        prv = {r["query"]: r for r in query(svc, site, prev_start, prev_end, ["query"])}
        deltas = []
        for q in set(cur) | set(prv):
            c, p = cur.get(q), prv.get(q)
            deltas.append({
                "query": q,
                "clicks": (c or {}).get("clicks", 0),
                "clicks_prev": (p or {}).get("clicks", 0),
                "d_clicks": (c or {}).get("clicks", 0) - (p or {}).get("clicks", 0),
                "impressions": (c or {}).get("impressions", 0),
                "d_impressions": (c or {}).get("impressions", 0) - (p or {}).get("impressions", 0),
            })
        deltas.sort(key=lambda r: r["d_clicks"])
        print("跌幅 Top15:")
        for r in deltas[:15]:
            print(f"  {r['d_clicks']:+4}  {r['query'][:60]}")
        print("涨幅 Top15:")
        for r in deltas[-15:][::-1]:
            print(f"  {r['d_clicks']:+4}  {r['query'][:60]}")
        save("compare", deltas)
    elif cmd == "dump":
        save("queries", query(svc, site, start, end, ["query"]))
        save("pages", query(svc, site, start, end, ["page"]))
        save("query-page", query(svc, site, start, end, ["query", "page"], limit=1000))
        save("dates", query(svc, site, start, end, ["date"]))
        save("countries", query(svc, site, start, end, ["country"]))
        save("devices", query(svc, site, start, end, ["device"]))
        print("全量导出完成 → ops/gsc/out/")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
