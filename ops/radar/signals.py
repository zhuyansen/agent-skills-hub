"""The two radar signals read from our own data: GitHub repos in the catalog, GSC queries.

github_surge   terms in the names and descriptions of repos created in the last 3 days,
               against repos created in the 30 days before, counted per owner. Repos are
               picked by GitHub creation date, not by first_seen: the extra_repos backfill
               adds old repos every sync and would read as a wave.
gsc_new        queries with impressions in the last 3 days and none in the 56 before. Reads
               GSC's fresh data (dataState=all): one day behind instead of three, at the
               cost of numbers GSC still revises; the radar only needs "seen or not".
"""
from __future__ import annotations

import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from terms import by_source, surges

ROOT = Path(__file__).resolve().parents[2]
RECENT_DAYS, BASELINE_DAYS = 3, 30
GH_MIN_OWNERS = 5
GSC_LAG_DAYS = 1
GSC_RECENT, GSC_BEFORE = 3, 56
GSC_MIN_IMPRESSIONS = 3
TOP = 25
_ROWS = """
SELECT author_name, repo_name || ' ' || coalesce(description, ''), created_at >= now() - make_interval(days => :recent)
FROM skills WHERE created_at >= now() - make_interval(days => :total)
"""


def db_url() -> str:
    return os.environ.get("SUPABASE_DB_URL") or next(
        m.group(1).strip() for line in (ROOT / "backend/.env").read_text().splitlines()
        if (m := re.match(r'\s*SUPABASE_DB_URL\s*=\s*["\']?([^"\'\n]+)', line)))


def github_rows() -> list[tuple]:
    """One light read on an indexed column; never during a heavy DB job (caller checks)."""
    from sqlalchemy import create_engine, text
    engine = create_engine(db_url().replace("postgres://", "postgresql://", 1), pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = '60s'"))
        rows = conn.execute(text(_ROWS), {"recent": RECENT_DAYS, "total": RECENT_DAYS + BASELINE_DAYS}).fetchall()
    engine.dispose()
    return rows


def distinct(rows: list[tuple]) -> list[tuple]:
    """One row per description: classroom templates (GitHub Skills "Exercise: ...") are
    copied by dozens of students with the text unchanged and would read as a wave."""
    seen, out = set(), []
    for owner, text, new in rows:
        key = text.split(" ", 1)[-1].strip().lower() or text
        if key not in seen:
            seen.add(key)
            out.append((owner, text, new))
    return out


def github_surge() -> dict:
    rows = distinct(github_rows())
    recent = by_source([(owner, text) for owner, text, new in rows if new])
    baseline = by_source([(owner, text) for owner, text, new in rows if not new])
    examples = {}
    for owner, text, new in rows:
        if new:
            examples.setdefault(owner, text)
    top = surges(recent, baseline, RECENT_DAYS / BASELINE_DAYS, GH_MIN_OWNERS, TOP)
    for r in top:
        r["examples"] = [examples[o][:90] for o in sorted(recent[r["term"]])[:3]]
    return {"repos_recent": sum(1 for *_, new in rows if new), "repos_baseline": sum(1 for *_, new in rows if not new),
            "terms": top}


def gsc_new() -> dict:
    sys.path.insert(0, str(ROOT / "ops/gsc"))
    import fetch_gsc as g
    svc = g.get_service()
    site = g.pick_site(svc)
    end = date.today() - timedelta(days=GSC_LAG_DAYS)
    start = end - timedelta(days=GSC_RECENT - 1)
    recent = g.query(svc, site, start, end, ["query", "page"], limit=25000, data_state="all")
    before = g.query(svc, site, start - timedelta(days=GSC_BEFORE), start - timedelta(days=1), ["query"], limit=25000)
    seen = {r["query"] for r in before}
    fresh: dict[str, dict] = {}
    for r in recent:
        if r["query"] in seen:
            continue
        f = fresh.setdefault(r["query"], {"query": r["query"], "impressions": 0, "clicks": 0, "page": r["page"]})
        f["impressions"] += r["impressions"]
        f["clicks"] += r["clicks"]
    rows = sorted((f for f in fresh.values() if f["impressions"] >= GSC_MIN_IMPRESSIONS), key=lambda f: -f["impressions"])
    return {"window": f"{start}..{end}", "queries": rows[:TOP], "total_new": len(fresh)}
