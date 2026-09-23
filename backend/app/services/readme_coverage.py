"""Which repos still need their README fetched, and how a fetch result is recorded.

The sync (scheduler/jobs.py Phase 5) and the backfill (backend/readme_backfill.py)
both select targets by this rule and write results through it, so they cannot
disagree about a repo's state:

    readme_content NULL                         never fetched: a target
    readme_content ''   + readme_fetched_at     GitHub had no README when asked:
                                                a target again after NO_README_RETRY_DAYS
    readme_content ''   + no readme_fetched_at  '' written before the marker existed
                                                (June backfill, extra_repos artifacts): a target
    readme_content text                         fetched: never a target

Pure: imported by the backfill job, which installs only psycopg2.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

NO_README_RETRY_DAYS = 30

# The same rule for SQL WHERE clauses. It is never NULL, so NOT (...) is safe.
MISSING_README_SQL = (
    "(readme_content IS NULL OR (readme_content = '' AND (readme_fetched_at IS NULL "
    f"OR readme_fetched_at < now() - interval '{NO_README_RETRY_DAYS} days')))"
)


def readme_missing(content: str | None, fetched_at: datetime | None, now: datetime) -> bool:
    if content is None:
        return True
    if content:
        return False
    return fetched_at is None or fetched_at < now - timedelta(days=NO_README_RETRY_DAYS)


def readme_update(current: str | None, fetched: str | None, absent: bool, now: Any) -> dict[str, Any]:
    """Column values for one fetch result.

    fetched: README text from a 200. absent: GitHub said there is none (404, or a
    200 with nothing in it). A real README is never replaced by '' — a 404 for a
    repo we hold text for is likelier a rename or a blip than a deleted README.
    `now` is a datetime in tests and func.now() in the sync, so the stamp comes
    from the database clock that grade_refresh compares it with.
    """
    if fetched:
        return {"readme_content": fetched, "readme_size": len(fetched), "readme_fetched_at": now}
    if absent and not current:
        return {"readme_content": "", "readme_size": 0, "readme_fetched_at": now}
    return {}
