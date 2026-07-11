#!/usr/bin/env python3
"""Chunked backfill of skills.readme_search_vector (~133K rows).

Scar this obeys: scan_all once ran 106K rows in ONE transaction -> 57014
statement_timeout -> full rollback (fixed in b7f83f0 by chunking). Same rule
here: small id-range batches, commit each, sleep between, resumable.

Run OFF-PEAK and never overlapping a sync (Supabase fragility discipline):
  cd backend && source venv/bin/activate && python ../ops/backfill_readme_search_vector.py
"""

import os
import sys
import time

import psycopg2
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, "backend", ".env"))

BATCH = 1500          # rows per UPDATE — well under statement_timeout
SLEEP = 0.6           # breathing room between batches (don't saturate pooler)


def connect():
    return psycopg2.connect(
        os.environ["SUPABASE_DB_URL"],
        connect_timeout=15,
        options="-c statement_timeout=55000",
        keepalives=1,
        keepalives_idle=30,
    )


def main() -> int:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT min(id), max(id) FROM skills")
    lo, hi = cur.fetchone()
    print(f"id range {lo}..{hi}, batch={BATCH}")

    done = 0
    start = lo
    while start <= hi:
        end = start + BATCH - 1
        try:
            cur.execute(
                """
                UPDATE skills SET readme_search_vector =
                    setweight(to_tsvector('english', COALESCE(repo_name, '')), 'A') ||
                    setweight(to_tsvector('english', COALESCE(description, '')), 'B') ||
                    setweight(to_tsvector('english', LEFT(COALESCE(readme_content, ''), 100000)), 'C')
                WHERE id BETWEEN %s AND %s
                  AND readme_search_vector IS NULL
                """,
                (start, end),
            )
            conn.commit()
            done += cur.rowcount
            if cur.rowcount:
                print(f"  [{start}-{end}] +{cur.rowcount} (total {done})")
        except Exception as exc:  # reconnect-and-resume, never abort the run
            print(f"  [{start}-{end}] error: {exc} — reconnecting")
            try:
                conn.close()
            except Exception:
                pass
            time.sleep(5)
            conn = connect()
            cur = conn.cursor()
            continue  # retry same window
        start = end + 1
        time.sleep(SLEEP)

    cur.execute("SELECT count(*) FROM skills WHERE readme_search_vector IS NULL")
    print(f"done: {done} rows filled, {cur.fetchone()[0]} still NULL (no readme rows stay NULL-safe)")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
