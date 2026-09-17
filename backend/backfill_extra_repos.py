"""Top up the extra_repos backfill queue, then let the sync that follows fetch it.

.github/workflows/sync.yml runs this in the sync job, right before
sync_runner.py, so its writes can never overlap a sync. It is idempotent: a
rerun with no sync in between changes nothing, and once every candidate has
been ingested or given up on it does nothing. Lifecycle and rationale are in
app/services/extra_repo_backfill.py.

Usage:
  cd backend
  python backfill_extra_repos.py            # apply
  python backfill_extra_repos.py --dry-run  # print the plan, write nothing
"""
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("backfill_extra_repos")

# The queue lives in the production catalog; unlike sync_runner.py there is no
# useful local-SQLite fallback, so refuse rather than write somewhere harmless.
if not os.environ.get("SUPABASE_DB_URL", "").strip():
    logger.error("SUPABASE_DB_URL is not set; the backfill queue only exists in Supabase")
    sys.exit(1)
os.environ["DATABASE_URL"] = os.environ["SUPABASE_DB_URL"].strip()

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.services.extra_repo_backfill import (  # noqa: E402
    BACKFILL_TAG,
    ExistingRow,
    load_candidates,
    plan_backfill,
)

# Only a handful of small statements. On this instance, failing fast is better
# than queueing behind a lock that a sync is holding.
STATEMENT_TIMEOUT = "15s"
LOCK_TIMEOUT = "5s"
RECENT_SYNCS = 50


def fetch_existing(db, candidates):
    """extra_repos rows matching a candidate, keyed by lowercased name."""
    starts = [r[0] for r in db.execute(text(
        "SELECT started_at FROM sync_logs WHERE status = 'completed' ORDER BY started_at DESC LIMIT :n"
    ), {"n": RECENT_SYNCS})]
    rows = db.execute(text(
        "SELECT full_name, is_active, submitted_by, reviewed_at FROM extra_repos WHERE lower(full_name) = ANY(:names)"
    ), {"names": [c.lower() for c in candidates]})
    existing = {}
    for full_name, is_active, submitted_by, activated_at in rows:
        syncs = sum(1 for s in starts if activated_at is not None and s > activated_at)
        existing[full_name.lower()] = ExistingRow(full_name, bool(is_active), submitted_by == BACKFILL_TAG, syncs)
    return existing


def fetch_catalog_state(db, candidates):
    """(in skills, in skills with a README), as lowercased names. Exact match keeps
    this on the unique index; candidate names come from the GitHub API, which is
    also where sync gets them."""
    rows = db.execute(text(
        "SELECT repo_full_name, (readme_content IS NOT NULL AND readme_content <> '') "
        "FROM skills WHERE repo_full_name = ANY(:names)"
    ), {"names": candidates}).fetchall()
    return {r[0].lower() for r in rows}, {r[0].lower() for r in rows if r[1]}


def apply_plan(db, plan):
    retire = plan.retire_ingested + plan.retire_stuck
    if retire:
        db.execute(text(
            "UPDATE extra_repos SET is_active = false WHERE submitted_by = :tag AND full_name = ANY(:names)"
        ), {"tag": BACKFILL_TAG, "names": retire})
    if plan.activate:
        db.execute(text(
            "INSERT INTO extra_repos (full_name, is_active, status, submitted_by, reviewed_at) "
            "VALUES (:name, true, 'approved', :tag, timezone('utc', now())) ON CONFLICT (full_name) DO NOTHING"
        ), [{"name": n, "tag": BACKFILL_TAG} for n in plan.activate])
    db.commit()


def report(plan, total):
    logger.info(
        "backfill %s: %d/%d in skills | retired now: %d with README, %d given up | in flight: %d | activating: %d | queued: %d",
        BACKFILL_TAG, plan.ingested_total, total, len(plan.retire_ingested), len(plan.retire_stuck),
        plan.in_flight, len(plan.activate), plan.queued,
    )
    for name in plan.retire_stuck:
        logger.warning("given up (not in skills, or no README, after enough syncs): %s", name)


def main():
    dry_run = "--dry-run" in sys.argv
    candidates = load_candidates()
    db = SessionLocal()
    try:
        db.execute(text(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'"))
        db.execute(text(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT}'"))
        in_catalog, with_readme = fetch_catalog_state(db, candidates)
        plan = plan_backfill(candidates, in_catalog, with_readme, fetch_existing(db, candidates))
        report(plan, len(candidates))
        if dry_run:
            logger.info("dry run: nothing written. would activate: %s", plan.activate[:10])
        elif plan.activate or plan.retire_ingested or plan.retire_stuck:
            apply_plan(db, plan)
            logger.info("applied")
    finally:
        db.close()


if __name__ == "__main__":
    main()
