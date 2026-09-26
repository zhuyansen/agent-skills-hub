"""Small, pure decisions the sync makes about what to fetch.

Kept out of scheduler/jobs.py so they can be unit-tested without a database or
the GitHub API.
"""
from __future__ import annotations

# Repos seen in a sync that have no README yet get one, most-starred first.
# Each fetch costs ~0.75s with the rate-limit pause, so 400 adds about 5 minutes;
# the slowest syncs already take ~97 of the job's 120-minute timeout.
README_FETCH_LIMIT = 400


def with_push_filter(query: str, pushed_filter: str) -> str:
    """Add the incremental pushed:> filter, except to queries bounded by creation date.

    Incremental syncs only ask for repos pushed since the last run. A query that
    targets a dated wave of new repos (e.g. everything built on a model since its
    launch) must not get that filter: most of the wave was pushed before the query
    existed and would never be found. created:> already bounds such a query.
    """
    if not pushed_filter or "created:>" in query:
        return query
    return query + pushed_filter


def select_readme_targets(
    all_repos: dict[str, dict], have_readme: set[str], limit: int = README_FETCH_LIMIT
) -> set[str]:
    """Repos seen in this sync without a README yet, most-starred first, capped.

    That covers new repos and existing rows that never got one. No README means
    the scanner can't grade the repo. New rows used to wait for a later sync
    that fetched them again, and most never were: the 2026-09-17 12:56 sync
    inserted 369 rows and fetched 8 READMEs. Existing rows fell outside the
    top-1000-by-score pass: Dicklesworthstone/skillranker, listed on
    /best/typesafe-jev/ and returned by every sync, stayed ungraded although
    GitHub has its 113KB README.
    """
    missing = [name for name in all_repos if name not in have_readme]
    missing.sort(key=lambda name: -(all_repos[name].get("stargazers_count") or 0))
    return set(missing[:limit])


# A wave query (created:>=) returns thousands of repos, sorted by stars, and the
# sync reads 300. The top 300 covers everything a scenario page shows (>=50 stars),
# but the 20-199 star tail — the repos the wave page will list next month — never
# enters. Two star bands, each read to the same 3-page cap, catch it.
WAVE_STAR_BANDS = ("stars:50..199", "stars:20..49")


def wave_slices(query: str) -> list[str]:
    if "created:>" not in query:
        return []
    return [f"{query} {band}" for band in WAVE_STAR_BANDS]


# Search results come sorted by stars, 100 per page. Three pages lost real repos:
# in one 8-hour push window `claude-code in:topics` had 326 repos with >=50 stars
# and `mcp-server` 611 with >=1 — 13 of 40 queries were cut at 300 every sync.
# Keep paging while the page is full, its last row still has a star, and GitHub's
# 1,000-result ceiling is not reached; the 0-star tail is not worth the requests.
MAX_SEARCH_PAGES = 10
PAGE_SIZE = 100


def keep_paging(page: int, items: list[dict]) -> bool:
    if len(items) < PAGE_SIZE or page >= MAX_SEARCH_PAGES:
        return False
    return (items[-1].get("stargazers_count") or 0) > 0
