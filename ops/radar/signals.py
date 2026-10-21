"""The radar signal read from our own data: GitHub repos in the catalog.

github_surge   terms in the names and descriptions of repos created in the last 3 days,
               against repos created in the 30 days before, counted per owner. Repos are
               picked by GitHub creation date, not by first_seen: the extra_repos backfill
               adds old repos every sync and would read as a wave. In shadow mode while
               GITHUB_SHOW is off (radar.shadow): recorded for the review, never shown.

New GSC queries (the former gsc_new) left the radar on 2026-10-21, for the weekly SEO review.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from terms import by_source, surges

ROOT = Path(__file__).resolve().parents[2]
# Off: the words new repos share are kept in radar_leads for the 14-day review and never shown (radar.shadow).
# Turn it on only after the review shows early hits for "②GitHub" in the daily report's hit-rate table (Trends
# rose a day or more after the radar saw the word); its words then go through Jev and into the reports again.
GITHUB_SHOW = False
RECENT_DAYS, BASELINE_DAYS = 3, 30
GH_MIN_OWNERS = 5
# A word already common in the 30-day baseline that only doubles is noise (pytorch 5 owners
# x2.6, instagram 16 x2.0 on 10-20); a real wave is either steep or wide (falkor x4.5,
# hyperframes 58-65 owners at x2-3, remotion 30+ at x2 in October).
GH_MIN_LIFT = 3.0
GH_WIDE_OWNERS = 20
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
        conn.execute(text("SET LOCAL statement_timeout = '60s'"))
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
    top = [r for r in surges(recent, baseline, RECENT_DAYS / BASELINE_DAYS, GH_MIN_OWNERS, TOP)
           if r["lift"] >= GH_MIN_LIFT or r["recent"] >= GH_WIDE_OWNERS]
    for r in top:
        r["examples"] = [examples[o][:90] for o in sorted(recent[r["term"]])[:3]]
    return {"repos_recent": sum(1 for *_, new in rows if new), "repos_baseline": sum(1 for *_, new in rows if not new),
            "terms": top}
