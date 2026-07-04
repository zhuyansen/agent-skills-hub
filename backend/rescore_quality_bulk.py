"""Bulk re-score of quality_* fields — same math as rescore_quality.py but ~100x
faster: one UPDATE ... FROM (VALUES ...) per chunk instead of 300 ORM row
UPDATEs (0.7s/row over the wire made the stars<5 long tail a 20-hour run that
would have collided with the 8-hourly sync; this finishes in well under an hour).

Usage: python rescore_quality_bulk.py [--min-stars 0] [--max-stars 5] [--start-id N]
"""
import logging
import os
import sys
import time

from dotenv import load_dotenv
load_dotenv("/Users/zhuyansen/content/agent-skills-hub/backend/.env")

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.models.skill import Skill  # noqa: E402
from app.services.quality_analyzer import QualityAnalyzer  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("rescore-bulk")

CHUNK = 300
MAX_RETRY = 5

def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default

MIN_STARS = arg("--min-stars", 0)
MAX_STARS = arg("--max-stars", 5)   # exclusive; -1 = unbounded
start_id = arg("--start-id", 0)

FIELDS = [
    "quality_score", "quality_completeness", "quality_clarity",
    "quality_specificity", "quality_examples", "quality_agent_readiness",
    "readme_structure_score",
]

def make_session():
    eng = create_engine(os.environ["SUPABASE_DB_URL"], pool_pre_ping=True, pool_recycle=300)
    return sessionmaker(bind=eng)()

def bulk_update_sql(rows):
    """One statement for the whole chunk. Values are floats/ints we computed —
    no user input, literal interpolation is safe here."""
    values = ",".join(
        "(%d,%s)" % (r[0], ",".join("%.4f" % v for v in r[1:]))
        for r in rows
    )
    cols = ",".join(FIELDS)
    sets = ",".join(f"{f} = v.{f}" for f in FIELDS)
    return f"UPDATE skills AS s SET {sets} FROM (VALUES {values}) AS v(id,{cols}) WHERE s.id = v.id"

def main():
    qa = QualityAnalyzer()
    db = make_session()
    last_id, total, t0 = start_id, 0, time.time()
    while True:
        for attempt in range(1, MAX_RETRY + 1):
            try:
                q = (db.query(Skill)
                     .filter(Skill.stars >= MIN_STARS, Skill.id > last_id))
                if MAX_STARS >= 0:
                    q = q.filter(Skill.stars < MAX_STARS)
                chunk = q.order_by(Skill.id.asc()).limit(CHUNK).all()
                rows = []
                for s in chunk:
                    qa._analyze(s)  # mutates in memory
                    rows.append((
                        s.id,
                        s.quality_score or 0, s.quality_completeness or 0,
                        s.quality_clarity or 0, s.quality_specificity or 0,
                        s.quality_examples or 0, s.quality_agent_readiness or 0,
                        s.readme_structure_score or 0,
                    ))
                db.rollback()  # drop ORM dirty state — the bulk stmt is the ONLY write
                if rows:
                    db.execute(text(bulk_update_sql(rows)))
                    db.commit()
                break
            except OperationalError:
                db.rollback()
                wait = min(2 ** attempt, 30)
                log.warning(f"  conn dropped (attempt {attempt}/{MAX_RETRY}) @ id>{last_id}; retry in {wait}s")
                try:
                    db.close()
                except Exception:
                    pass
                time.sleep(wait)
                db = make_session()
                if attempt == MAX_RETRY:
                    log.error(f"  giving up at id>{last_id}; resume with --start-id {last_id}")
                    db.close()
                    return
        else:
            continue
        if not chunk:
            break
        total += len(chunk)
        last_id = chunk[-1].id
        rate = total / max(time.time() - t0, 1)
        log.info(f"  re-scored {total} (last_id={last_id}, {rate:.0f} rows/s)")
        if len(chunk) < CHUNK:
            break
        time.sleep(0.2)  # gentle on the pooler
    db.close()
    log.info(f"✓ done: {total} skills re-scored ({MIN_STARS} <= stars < {MAX_STARS}) in {time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
