"""Remove clone campaigns from the catalog: one real project's README copied under many
throwaway accounts, every copy with bought stars.

The OpenSEO audit of 2026-11-18 found ~900 such rows with live /skill/ pages graded safe:
Simpleyyt/ai-manus' description under "ai--manus", "manus--ai", "ai--manus2.0"…, the GitHub
Copilot app's under "GitHub-Copilot-app", a Gemini proxy scanner and a "Capri" desktop
agent, each README a "GET" button to a .rar on Dropbox. The search queries find them again
on every sync, so this runs after every upsert, beside the case-dedup backstop.

The rule (frontend/scripts/clone-campaigns.mjs applies the same one to the build, and
tests/test_clone_campaigns.py checks the constants agree):
  - the same description (case and spacing ignored, at least MIN_DESC chars)
  - on at least MIN_OWNERS different accounts
  - and every copy has at least MIN_STARS stars. Forks and course copies of a real project
    share its description too, but sit at 0–1 stars, so they never match.
The original is kept when it predates the rest of its group by ORIGINAL_LEAD_DAYS.
Rows in user_favorites and arena_votes go with them (ON DELETE CASCADE).
"""
from __future__ import annotations

MIN_DESC = 30
MIN_OWNERS = 5
MIN_STARS = 20
ORIGINAL_LEAD_DAYS = 30

_PARAMS = {"min_desc": MIN_DESC, "min_owners": MIN_OWNERS, "min_stars": MIN_STARS,
           "lead": f"{ORIGINAL_LEAD_DAYS} days"}

# Every row of every campaign group, minus each group's original.
_CAMPAIGN_ROWS = """
    WITH s AS (
        SELECT id, created_at, stars, d,
               lower(coalesce(nullif(author_name, ''), split_part(repo_full_name, '/', 1))) AS owner
        FROM (SELECT id, created_at, stars, author_name, repo_full_name,
                     lower(btrim(regexp_replace(coalesce(description, ''), '\\s+', ' ', 'g'))) AS d
              FROM skills) n
        WHERE length(d) >= %(min_desc)s
    ),
    campaign AS (
        SELECT d FROM s GROUP BY d
        HAVING count(DISTINCT owner) >= %(min_owners)s AND min(stars) >= %(min_stars)s
    ),
    ranked AS (
        SELECT s.id, s.created_at,
               row_number() OVER w AS rn,
               lead(s.created_at) OVER w AS next_created
        FROM s JOIN campaign USING (d)
        WINDOW w AS (PARTITION BY s.d ORDER BY s.created_at NULLS LAST, s.id)
    )
    SELECT id FROM ranked
    WHERE NOT (rn = 1 AND next_created - created_at >= %(lead)s::interval)
"""

COUNT_SQL = f"SELECT count(*) FROM ({_CAMPAIGN_ROWS}) c"
DELETE_SQL = f"DELETE FROM skills WHERE id IN ({_CAMPAIGN_ROWS})"


def count(cursor) -> int:
    """Rows the next cleanup would delete (a DB-API cursor: psycopg2 or SQLAlchemy raw)."""
    cursor.execute(COUNT_SQL, _PARAMS)
    return cursor.fetchone()[0]


def delete(cursor) -> int:
    """Delete them; returns how many. The caller commits."""
    cursor.execute(DELETE_SQL, _PARAMS)
    return cursor.rowcount
