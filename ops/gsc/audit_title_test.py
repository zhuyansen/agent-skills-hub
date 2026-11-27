"""Result of the /audit/ title test (ops/geo/experiments.json, id audit-title-grade-date).

From the test's start a stable 10% of audit pages put the grade and the month of the scan in
their title (frontend/scripts/audit-meta.mjs). This reads Search Console and says whether those
pages gained clicks or CTR against the rest.

Groups: the rule the build uses, recomputed here from frontend/scripts/audit-title-test.json
(bucket of the lowercased owner/repo < share_percent -> treated; listed repos -> excluded).

Primary metric: clicks and CTR per group, the PRE_DAYS before the start against the start to
--end, on the pages that had impressions before the start (the same pages in both periods,
so new or dropped pages don't move a group). The estimate is the difference in differences
of CTR, with a 95% bootstrap interval that resamples pages. Average position is reported too:
a title can move the ranking as well as the click rate.

Secondary metric (GA4, skipped with --no-ga or without ops/ga/adc.json): page views of
/analyzer/ and /skill/ whose referrer is an audit page, per group and period, i.e. clicks on
"Run a live scan" and "Full details & install". Same automation filter as fetch_ga.py.

Usage (from backend/ with its venv, like fetch_gsc.py; reads ops/gsc/token.json):
  python ../ops/gsc/audit_title_test.py                     # start from the test file, end = 3 days ago
  python ../ops/gsc/audit_title_test.py --end 2027-01-10    # the six-week read-out
  python ../ops/gsc/audit_title_test.py --start 2026-10-26 --end 2026-11-22 --no-ga   # an A/A check on old data

Writes ops/gsc/out/audit-title-test-<end>.json. Search Console finalises a day about three days
after it ends, so --end defaults to three days ago.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
TEST_FILE = REPO / "frontend" / "scripts" / "audit-title-test.json"
PRE_DAYS = 28
FINAL_AFTER_DAYS = 3
BOOTSTRAP = 2000
GROUPS = ("treated", "control")
AUDIT_URL = re.compile(r"^https://agentskillshub\.top/audit/([^/?#]+/[^/?#]+)/$")
MASK = 0xFFFFFFFF


# ── assignment: the same arithmetic as frontend/scripts/related-links.mjs + audit-meta.mjs ──

def fnv1a32(text: str) -> int:
    h = 0x811C9DC5
    for ch in text:
        h ^= ord(ch)
        h = (h * 0x01000193) & MASK
    return h


def _imul(a: int, b: int) -> int:
    return (a * b) & MASK


def mulberry32_first(seed: int) -> int:
    t = (seed + 0x6D2B79F5) & MASK
    t = _imul(t ^ (t >> 15), t | 1)
    t ^= (t + _imul(t ^ (t >> 7), t | 61)) & MASK
    return (t ^ (t >> 14)) & MASK


def title_bucket(full_name: str, test_id: str) -> int:
    return mulberry32_first(fnv1a32(f"{test_id}|{full_name.lower()}")) % 100


def load_test(path: Path = TEST_FILE) -> dict:
    test = json.loads(path.read_text("utf-8"))
    test["excluded_set"] = {n.lower() for n in test["excluded"]}
    return test


def group_of(url: str, test: dict) -> str | None:
    """treated / control / excluded for an audit page URL, None for any other URL."""
    m = AUDIT_URL.match(url)
    if not m:
        return None
    name = m.group(1).lower()
    if name in test["excluded_set"]:
        return "excluded"
    return "treated" if title_bucket(name, test["id"]) < test["share_percent"] else "control"


# ── arithmetic on {url: {"clicks", "impressions", "position"}} ──

def totals(rows: list[dict]) -> dict:
    clicks = sum(r["clicks"] for r in rows)
    impressions = sum(r["impressions"] for r in rows)
    weighted = sum(r["position"] * r["impressions"] for r in rows)
    return {
        "pages": len(rows),
        "clicks": clicks,
        "impressions": impressions,
        "ctr_pct": round(100 * clicks / impressions, 3) if impressions else None,
        "position": round(weighted / impressions, 2) if impressions else None,
    }


def ctr_change(pages: list[tuple[dict, dict]]) -> float | None:
    """CTR after minus CTR before, in percentage points, over (pre, post) rows of the same pages."""
    pre_i = sum(p["impressions"] for p, _ in pages)
    post_i = sum(q["impressions"] for _, q in pages)
    if not pre_i or not post_i:
        return None
    return 100 * (sum(q["clicks"] for _, q in pages) / post_i - sum(p["clicks"] for p, _ in pages) / pre_i)


def did(paired: dict[str, list[tuple[dict, dict]]]) -> float | None:
    t, c = ctr_change(paired["treated"]), ctr_change(paired["control"])
    return None if t is None or c is None else t - c


def bootstrap_interval(paired: dict[str, list], reps: int = BOOTSTRAP, seed: int = 1) -> tuple[float, float] | None:
    """95% interval of did() when each group's pages are resampled with replacement."""
    rng = random.Random(seed)
    draws = []
    for _ in range(reps):
        sample = {g: [rng.choice(paired[g]) for _ in paired[g]] for g in GROUPS if paired[g]}
        if len(sample) == len(GROUPS) and (d := did(sample)) is not None:
            draws.append(d)
    if len(draws) < reps // 2:
        return None
    draws.sort()
    return round(draws[int(0.025 * len(draws))], 3), round(draws[int(0.975 * len(draws)) - 1], 3)


def pair_pages(pre: dict, post: dict, test: dict) -> dict[str, list[tuple[dict, dict]]]:
    """Pages with impressions before the start, with their rows before and after, by group."""
    empty = {"clicks": 0, "impressions": 0, "position": 0.0}
    paired: dict[str, list] = {g: [] for g in (*GROUPS, "excluded")}
    for url, row in pre.items():
        group = group_of(url, test)
        if group and row["impressions"] > 0:
            paired[group].append((row, post.get(url, empty)))
    return paired


# ── Search Console and GA4 ──

def gsc_audit_pages(svc, site, start: dt.date, end: dt.date) -> dict[str, dict]:
    import fetch_gsc as gsc  # noqa: E402  (needs the Google auth libraries of the backend venv)
    flt = [{"dimension": "page", "operator": "contains", "expression": "/audit/"}]
    rows, start_row = [], 0
    while True:
        batch = gsc.query(svc, site, start, end, ["page"], filters=flt, limit=25000, start_row=start_row)
        rows += batch
        if len(batch) < 25000:
            break
        start_row += len(batch)
    return {r["page"]: {"clicks": r["clicks"], "impressions": r["impressions"], "position": r["position"]} for r in rows}


def ga_referrals(start: dt.date, end: dt.date, test: dict) -> dict | None:
    """page_view counts on /analyzer/ and /skill/ whose referrer is an audit page, by group."""
    sys.path.insert(0, str(HERE.parent / "ga"))
    try:
        import fetch_ga as ga  # noqa: E402
        sess = ga.session()
    except Exception as e:  # no creds, no libraries: say so rather than report zeros
        print(f"  GA4 skipped: {e}", file=sys.stderr)
        return None
    body = {
        "dateRanges": [{"startDate": str(start), "endDate": str(end)}],
        "dimensions": [{"name": "pageReferrer"}, {"name": "pagePath"}],
        "metrics": [{"name": "eventCount"}],
        "dimensionFilter": {"andGroup": {"expressions": [
            ga.traffic_filter(),
            {"filter": {"fieldName": "eventName", "stringFilter": {"matchType": "EXACT", "value": "page_view"}}},
            {"filter": {"fieldName": "pageReferrer", "stringFilter": {"matchType": "CONTAINS", "value": "agentskillshub.top/audit/"}}},
        ]}},
        "limit": 100000,
    }
    r = sess.post(f"{ga.API}:runReport", json=body, timeout=60)
    r.raise_for_status()
    out = {g: {"analyzer": 0, "skill": 0} for g in (*GROUPS, "excluded")}
    for row in r.json().get("rows", []):
        ref, path = (d["value"] for d in row["dimensionValues"])
        group = group_of(ref.split("?")[0].split("#")[0], test)
        kind = "analyzer" if path.startswith("/analyzer") else "skill" if path.startswith("/skill/") else None
        if group and kind:
            out[group][kind] += int(row["metricValues"][0]["value"])
    return out


def report(test: dict, start: dt.date, end: dt.date, pre: dict, post: dict, ga: dict | None) -> dict:
    paired = pair_pages(pre, post, test)
    return {
        "test": test["id"], "start": str(start), "end": str(end), "pre_days": PRE_DAYS,
        "groups": {g: {"before": totals([p for p, _ in rows]), "after": totals([q for _, q in rows])}
                   for g, rows in paired.items()},
        "did_ctr_pp": None if (d := did(paired)) is None else round(d, 3),
        "did_ctr_pp_95ci": bootstrap_interval(paired),
        "ga_referrals": ga,
    }


def print_report(res: dict) -> None:
    print(f"{res['test']}: before = {res['pre_days']} days to {res['start']}, after = {res['start']} … {res['end']}")
    print(f"{'group':9} {'pages':>6} {'clicks before→after':>22} {'impressions before→after':>27} {'CTR % before→after':>22} {'position':>13}")
    for g, v in res["groups"].items():
        b, a = v["before"], v["after"]
        print(f"{g:9} {b['pages']:>6} {b['clicks']:>10,} → {a['clicks']:<9,} {b['impressions']:>12,} → {a['impressions']:<12,} "
              f"{b['ctr_pct'] or 0:>9.2f} → {a['ctr_pct'] or 0:<9.2f} {b['position'] or 0:>5.1f} → {a['position'] or 0:<5.1f}")
    ci = res["did_ctr_pp_95ci"]
    print(f"Difference in differences of CTR (treated − control): {res['did_ctr_pp']} pp, 95% interval {ci}")
    if ci and ci[0] <= 0 <= ci[1]:
        print("  The interval includes 0: no difference this data can tell apart from noise.")
    for period, counts in (res["ga_referrals"] or {}).items():
        if counts:
            print(f"GA4 page views reached from audit pages, {period}: "
                  + ", ".join(f"{g} analyzer {c['analyzer']} · skill {c['skill']}" for g, c in counts.items()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    test = load_test()
    ap.add_argument("--start", default=test["start"])
    ap.add_argument("--end", default=str(dt.date.today() - dt.timedelta(days=FINAL_AFTER_DAYS)))
    ap.add_argument("--no-ga", action="store_true")
    args = ap.parse_args()
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)
    if end < start:
        sys.exit(f"--end {end} is before the start {start}: nothing to read yet.")
    sys.path.insert(0, str(HERE))
    import fetch_gsc as gsc  # noqa: E402
    svc = gsc.get_service()
    site = gsc.pick_site(svc)
    pre = gsc_audit_pages(svc, site, start - dt.timedelta(days=PRE_DAYS), start - dt.timedelta(days=1))
    post = gsc_audit_pages(svc, site, start, end)
    ga = None if args.no_ga else {"after": ga_referrals(start, end, test),
                                  "before": ga_referrals(start - dt.timedelta(days=PRE_DAYS), start - dt.timedelta(days=1), test)}
    res = report(test, start, end, pre, post, ga)
    print_report(res)
    out = HERE / "out" / f"audit-title-test-{end}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"→ {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
