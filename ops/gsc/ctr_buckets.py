"""Click-through by position bucket, cut by device and page type, from query x page x country x
device rows.

Why: a site-wide CTR mixes position 2 with position 9. The trial exhibits in U.S. v. Google read
clicks per query x URL, split by country and device, and compare them only at the same position
(Tr. 6412-6413, PXR0357). This reads ours the same way: CTR inside each position bucket, then the
same buckets per device and per page type, each set against the whole site's CTR at that bucket
("vs site": 1.00 = what the site gets at those positions). The 11-14 title review reads it.

Rows are paged past the API's 25,000-row cap and saved to ops/gsc/out/ (gitignored). Search-
operator queries are dropped (fetch_gsc.is_operator_query). Query-level rows never hold the
anonymised queries, so the coverage line compares their totals with the property's own.

Usage (backend venv, Clash proxy on):
  export https_proxy=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897
  python ops/gsc/ctr_buckets.py [--days 28] [--end YYYY-MM-DD] [--page-contains /skill/]
"""
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_gsc import arg, get_service, is_operator_query, pick_site, query, save  # noqa: E402

DIMENSIONS = ["query", "page", "country", "device"]
PAGE_SIZE = 25000          # the API's per-request maximum
FINAL_DATA_LAG_DAYS = 3    # GSC's final numbers trail by about three days
BUCKETS = ((1, 3), (4, 6), (7, 10), (11, 20), (21, None))
MIN_RATIO_IMPRESSIONS = 200  # below this a cell's few clicks make its "vs site" ratio noise
SITE_PREFIX = "https://agentskillshub.top"


def bucket_of(position):
    """Label of the position bucket a row's average position falls in ("1-3" ... "21+")."""
    rank = round(position)
    for low, high in BUCKETS:
        if high is None or rank <= high:
            return f"{low}+" if high is None else f"{low}-{high}"
    return None


def page_type(url):
    path = url.replace(SITE_PREFIX, "") or "/"
    if path == "/":
        return "home"
    return next((t for t in ("/best/", "/skill/", "/compare/", "/category/") if path.startswith(t)), "other")


def fetch_rows(svc, site, start, end, filters):
    """Every query x page x country x device row in the window, search-operator queries included:
    paging needs the raw page sizes, so the caller drops them."""
    rows, start_row = [], 0
    while True:
        batch = query(svc, site, start, end, DIMENSIONS, filters, limit=PAGE_SIZE,
                      include_operators=True, start_row=start_row)
        rows += batch
        if len(batch) < PAGE_SIZE:
            return rows
        start_row += PAGE_SIZE


def tally(rows, key):
    """{group: {bucket: [impressions, clicks]}} for rows grouped by key(row)."""
    out = {}
    for r in rows:
        cell = out.setdefault(key(r), {}).setdefault(bucket_of(r["position"]), [0, 0])
        cell[0] += r["impressions"]
        cell[1] += r["clicks"]
    return out


def print_table(title, groups, site_ctr):
    print(f"\n{title}")
    labels = [f"{lo}+" if hi is None else f"{lo}-{hi}" for lo, hi in BUCKETS]
    for group, cells in sorted(groups.items(), key=lambda g: -sum(c[0] for c in g[1].values())):
        parts = []
        for label in labels:
            imp, clk = cells.get(label, (0, 0))
            ctr = clk / imp if imp else 0
            ratio = f" ×{ctr / site_ctr[label]:.2f}" if site_ctr and site_ctr.get(label) and imp >= MIN_RATIO_IMPRESSIONS else ""
            parts.append(f"{label} {imp:>6,.0f}次 {ctr:5.1%}{ratio}")
        print(f"  {str(group):<10} " + " | ".join(parts))


def coverage(svc, site, start, end, filters, rows, operator_impressions):
    total = query(svc, site, start, end, [], filters, limit=1)
    whole = total[0]["impressions"] if total else 0
    if not whole:
        print("  (无数据)")
        return
    imp = sum(r["impressions"] for r in rows)
    print(f"  下面的表覆盖 {imp:,.0f} / {whole:,.0f} 次曝光（{imp / whole:.0%}）；"
          f"剔除了搜索操作符查询 {operator_impressions:,.0f} 次，其余是匿名查询")


def main():
    end = date.fromisoformat(arg("--end", str(date.today() - timedelta(days=FINAL_DATA_LAG_DAYS))))
    start = end - timedelta(days=arg("--days", 28) - 1)
    contains = arg("--page-contains", "")
    filters = [{"dimension": "page", "operator": "contains", "expression": contains}] if contains else None
    svc = get_service()
    site = pick_site(svc)
    raw = fetch_rows(svc, site, start, end, filters)
    rows = [r for r in raw if not is_operator_query(r["query"])]
    print(f"{start} → {end}{'，网址含 ' + contains if contains else ''}：{len(rows):,} 行")
    coverage(svc, site, start, end, filters, rows, sum(r["impressions"] for r in raw) - sum(r["impressions"] for r in rows))
    scope = contains or "全站"
    overall = tally(rows, lambda r: scope)[scope]
    site_ctr = {label: clk / imp for label, (imp, clk) in overall.items() if imp}
    print_table("按位次分桶（点击率）", {scope: overall}, None)
    print_table("按设备（×n = 同位次全站点击率的倍数）", tally(rows, lambda r: r["device"]), site_ctr)
    print_table("按页型", tally(rows, lambda r: page_type(r["page"])), site_ctr)
    save(f"ctr-buckets-{start}_{end}{'-' + contains.strip('/').replace('/', '_') if contains else ''}", rows)


if __name__ == "__main__":
    main()
