"""Post-sync step: record Jev day-one priors for new repos and fill 14-day star outcomes.

Runs in sync.yml after the sync, in the same job, so it never overlaps a sync's writes.
Small and bounded by design (see memory: dont-overload-supabase): at most MAX_SCORE new
priors per run, each written in its own short transaction, and one UPDATE for outcomes.
A failure here must not fail the sync job (continue-on-error in the workflow).

Selection mirrors the public retrospective study: repos created at most 14 days before we
first saw them, first seen within the last LOOKBACK_DAYS, README longer than 300 chars."""

import json
import logging
import os
import sys

import httpx
from sqlalchemy import create_engine, text

from app.services.cold_start_prior import JevEndpoint, endpoint_from_env, score_prior

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("cold_start_priors")

MAX_SCORE = 150
LOOKBACK_DAYS = 3
OUTCOME_DAYS = 14
STATEMENT_TIMEOUT = "30s"
# The account, not the repo, was refused: every remaining call would get the same answer
# (from ~10-07 each run spent 150 calls on HTTP 402).
ACCOUNT_ERRORS = {401, 402, 403}

# Cheap filters first, README last. With `length(readme_content) > 300` in one WHERE, the
# planner checked the length before the date and read the README of most of the catalog
# (1.8 GB of TOAST); the query hit the 30 s timeout on 10-17 and 10-19. Here the length is
# a column of `recent`, so it is only computed for rows that passed the date filters, and
# from readme_size (len(readme), written with every README) unless that is missing. Only
# the picked rows have their README read.
NEW_REPOS = text("""
with recent as materialized (
  select id, repo_full_name, first_seen,
         coalesce(nullif(readme_size, 0), length(readme_content)) as readme_chars
  from skills
  where first_seen >= now() - make_interval(days => :lookback)
    and created_at >= first_seen - interval '14 days'
    and readme_content is not null
), picked as materialized (
  select r.id, r.first_seen
  from recent r
  left join cold_start_priors p on p.repo_full_name = r.repo_full_name
  where p.repo_full_name is null and r.readme_chars > 300
  order by r.first_seen desc, r.id desc   -- a sync batch shares one first_seen (45 at the cut on 10-20)
  limit :lim
)
select s.repo_full_name, s.author_name, s.description, s.category, s.stars,
       s.created_at, s.first_seen, left(s.readme_content, 4000) as readme
from picked join skills s on s.id = picked.id
order by picked.first_seen desc, picked.id desc
""")

INSERT_PRIOR = text("""
insert into cold_start_priors (repo_full_name, repo_created_at, first_seen, stars_at_score, model, prior)
values (:repo, :created, :seen, :stars, :model, cast(:prior as jsonb))
on conflict (repo_full_name) do nothing
""")

FILL_OUTCOMES = text("""
update cold_start_priors p
set stars_at_14d = s.stars,
    outcome_at = now(),
    outcome_stale = s.last_synced is null
                    or s.last_synced < p.scored_at + make_interval(days => :days) - interval '1 day'
from skills s
where s.repo_full_name = p.repo_full_name
  and p.stars_at_14d is null
  and p.scored_at <= now() - make_interval(days => :days)
""")


def _connect():
    engine = create_engine(os.environ["SUPABASE_DB_URL"], pool_pre_ping=True)
    return engine


def _new_repos(engine) -> list[dict]:
    with engine.connect() as conn:
        conn.execute(text(f"set local statement_timeout = '{STATEMENT_TIMEOUT}'"))
        rows = conn.execute(NEW_REPOS, {"lookback": LOOKBACK_DAYS, "lim": MAX_SCORE}).mappings().all()
    return [dict(r) for r in rows]


def _save_prior(engine, row: dict, prior: dict, model: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"set local statement_timeout = '{STATEMENT_TIMEOUT}'"))
        conn.execute(INSERT_PRIOR, {"repo": row["repo_full_name"], "created": row["created_at"],
                                    "seen": row["first_seen"], "stars": row["stars"] or 0,
                                    "model": model, "prior": json.dumps(prior)})


class AccountError(RuntimeError):
    """Jev refused the account itself (401/402/403), so no other repo can be scored either."""


def _score_one(engine, row: dict, endpoint: JevEndpoint, client: httpx.Client) -> bool:
    """Score and save one repo; False when it failed. Raises AccountError to stop the run."""
    try:
        prior, model = score_prior(row, endpoint, client)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in ACCOUNT_ERRORS:
            raise AccountError(f"HTTP {exc.response.status_code}") from exc
        log.warning("prior failed for %s: %s", row["repo_full_name"], exc)
        return False
    except (httpx.HTTPError, RuntimeError, KeyError) as exc:
        log.warning("prior failed for %s: %s", row["repo_full_name"], exc)
        return False
    _save_prior(engine, row, prior, model)
    return True


def _score_rows(engine, rows: list[dict], endpoint: JevEndpoint, stats: dict) -> None:
    with httpx.Client() as client:
        for row in rows:
            ok = _score_one(engine, row, endpoint, client)
            stats["scored" if ok else "failed"] += 1


def score_new(engine, endpoint: JevEndpoint) -> dict:
    rows = _new_repos(engine)
    stats = {"candidates": len(rows), "scored": 0, "failed": 0}
    try:
        _score_rows(engine, rows, endpoint, stats)
    except AccountError as exc:
        stats["stopped"] = str(exc)
        log.error("Jev refused the %s account (%s); stopping this run", endpoint.name, exc)
    return stats


def fill_outcomes(engine) -> int:
    with engine.begin() as conn:
        conn.execute(text(f"set local statement_timeout = '{STATEMENT_TIMEOUT}'"))
        return conn.execute(FILL_OUTCOMES, {"days": OUTCOME_DAYS}).rowcount


def main() -> int:
    endpoint = endpoint_from_env()
    if endpoint is None:
        log.warning("Neither TYPESAFE_API_KEY nor OPENROUTER_API_KEY is set; skipping cold-start priors")
        return 0
    engine = _connect()
    filled = fill_outcomes(engine)
    stats = score_new(engine, endpoint)
    log.info("cold-start priors via %s: %s, outcomes filled: %d", endpoint.name, stats, filled)
    # Candidates and not one prior is not a quiet day. Exit non-zero so the step shows as
    # failed (continue-on-error keeps the sync job green); it failed unseen from ~10-07.
    return 1 if stats["candidates"] and not stats["scored"] else 0


if __name__ == "__main__":
    sys.exit(main())
