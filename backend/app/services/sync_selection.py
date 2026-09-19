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
