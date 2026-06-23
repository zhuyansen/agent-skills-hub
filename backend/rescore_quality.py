"""Safe one-time re-score of quality_score for stars>=5 skills (v4 calibration).

Discipline (see memory: dont-overload-supabase, scan-all-single-transaction):
- Keyset pagination by id — NEVER db.query(Skill).all() on the 117K table.
- Small chunks (300) with a per-chunk commit — no single giant transaction.
- pool_pre_ping + reconnect-and-retry on the intermittent SSL drops.
- Resumable: pass --start-id N to continue after an interruption.
- Run ALONE — never overlap with a deploy/sync (both hammer the same DB).

Usage:  python rescore_quality.py [--start-id N] [--min-stars 5]
"""
import os, sys, time, logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from app.models.skill import Skill
from app.services.quality_analyzer import QualityAnalyzer

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("rescore")

CHUNK = 300
MAX_RETRY = 5

def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default

MIN_STARS = arg("--min-stars", 5)
start_id = arg("--start-id", 0)

def make_session():
    eng = create_engine(os.environ["SUPABASE_DB_URL"], pool_pre_ping=True, pool_recycle=300)
    return sessionmaker(bind=eng)()

def main():
    qa = QualityAnalyzer()
    db = make_session()
    last_id, total = start_id, 0
    while True:
        for attempt in range(1, MAX_RETRY + 1):
            try:
                chunk = (db.query(Skill)
                         .filter(Skill.stars >= MIN_STARS, Skill.id > last_id)
                         .order_by(Skill.id.asc())
                         .limit(CHUNK).all())
                for s in chunk:
                    qa._analyze(s)          # mutates quality_* fields in memory
                db.commit()                 # one commit per chunk
                break
            except OperationalError as e:
                db.rollback()
                wait = min(2 ** attempt, 30)
                log.warning(f"  conn dropped (attempt {attempt}/{MAX_RETRY}) @ id>{last_id}; reconnecting in {wait}s")
                try: db.close()
                except Exception: pass
                time.sleep(wait)
                db = make_session()
                if attempt == MAX_RETRY:
                    log.error(f"  giving up at id>{last_id}; resume with --start-id {last_id}")
                    db.close(); return
        else:
            continue
        if not chunk:
            break
        total += len(chunk)
        last_id = chunk[-1].id
        log.info(f"  re-scored {total} (last_id={last_id})")
        if len(chunk) < CHUNK:
            break
        time.sleep(0.3)  # gentle: don't hammer the pooler back-to-back
    db.close()
    log.info(f"✓ done: {total} skills re-scored (stars>={MIN_STARS})")

if __name__ == "__main__":
    main()
