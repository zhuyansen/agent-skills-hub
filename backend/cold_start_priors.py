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

from app.services.cold_start_prior import score_prior

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("cold_start_priors")

MAX_SCORE = 150
LOOKBACK_DAYS = 3
OUTCOME_DAYS = 14
STATEMENT_TIMEOUT = "30s"

NEW_REPOS = text("""
select s.repo_full_name, s.author_name, s.description, s.category, s.stars,
       s.created_at, s.first_seen, left(s.readme_content, 4000) as readme
from skills s
left join cold_start_priors p on p.repo_full_name = s.repo_full_name
where p.repo_full_name is null
  and s.first_seen >= now() - make_interval(days => :lookback)
  and s.created_at >= s.first_seen - interval '14 days'
  and s.readme_content is not null and length(s.readme_content) > 300
order by s.first_seen desc
limit :lim
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
        conn.execute(text(f"set statement_timeout = '{STATEMENT_TIMEOUT}'"))
        rows = conn.execute(NEW_REPOS, {"lookback": LOOKBACK_DAYS, "lim": MAX_SCORE}).mappings().all()
    return [dict(r) for r in rows]


def _save_prior(engine, row: dict, prior: dict, model: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"set local statement_timeout = '{STATEMENT_TIMEOUT}'"))
        conn.execute(INSERT_PRIOR, {"repo": row["repo_full_name"], "created": row["created_at"],
                                    "seen": row["first_seen"], "stars": row["stars"] or 0,
                                    "model": model, "prior": json.dumps(prior)})


def score_new(engine, api_key: str) -> dict:
    rows = _new_repos(engine)
    stats = {"candidates": len(rows), "scored": 0, "failed": 0}
    with httpx.Client() as client:
        for row in rows:
            try:
                prior, model = score_prior(row, api_key, client)
            except (httpx.HTTPError, RuntimeError, KeyError) as exc:
                stats["failed"] += 1
                log.warning("prior failed for %s: %s", row["repo_full_name"], exc)
                continue
            _save_prior(engine, row, prior, model)
            stats["scored"] += 1
    return stats


def fill_outcomes(engine) -> int:
    with engine.begin() as conn:
        conn.execute(text(f"set local statement_timeout = '{STATEMENT_TIMEOUT}'"))
        return conn.execute(FILL_OUTCOMES, {"days": OUTCOME_DAYS}).rowcount


def main() -> int:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        log.warning("OPENROUTER_API_KEY not set; skipping cold-start priors")
        return 0
    engine = _connect()
    filled = fill_outcomes(engine)
    stats = score_new(engine, api_key)
    log.info("cold-start priors: %s, outcomes filled: %d", stats, filled)
    return 0


if __name__ == "__main__":
    sys.exit(main())
