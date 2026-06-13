#!/usr/bin/env python3
"""
README backfill — fetch missing READMEs for quality skills (stars>=5) so the
existing SecurityScanner can grade them, driving down the ~99% `unknown` rate.

Concurrent: a thread pool fills the per-request latency gaps, while a single
global pacer keeps the *total* request rate just under GitHub's 5000/hr
(≈1.3/s) so we never trip 429s regardless of per-call latency. Resume-able
(only NULL readme), idempotent. A 404 (no README) writes "" so it isn't
retried and the scanner correctly leaves it ungraded.

Env:  GH_TOKEN (e.g. `gh auth token`), SUPABASE_DB_URL (from backend/.env)
Args: [max_count]  cap this run (default all); pass e.g. 100 to validate.
"""

import os
import re
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2

GH_TOKEN = os.environ["GH_TOKEN"].strip()
# Lowered from 8→4 after the 8-worker run + a concurrent trigram index build
# overloaded the Supabase instance (REST started 504-ing even on trivial
# queries, degrading the live site). 4 workers + 1s global pace keeps DB write
# pressure gentle while still ~5x the original single-thread rate.
WORKERS = 4
MIN_INTERVAL = 1.0  # seconds between request *starts*, globally → ≤1/s

_pace_lock = threading.Lock()
_last_start = [0.0]


def _pace():
    with _pace_lock:
        wait = MIN_INTERVAL - (time.time() - _last_start[0])
        if wait > 0:
            time.sleep(wait)
        _last_start[0] = time.time()


def db_url():
    for line in open(os.path.join(os.path.dirname(__file__), ".env")):
        m = re.match(r'\s*SUPABASE_DB_URL\s*=\s*["\']?([^"\'\n]+)', line)
        if m:
            return m.group(1).strip()
    return os.environ["SUPABASE_DB_URL"]


DB_URL = db_url()
_local = threading.local()


def conn():
    if not getattr(_local, "conn", None):
        _local.conn = psycopg2.connect(DB_URL)
        _local.conn.autocommit = True
    return _local.conn


def fetch_readme(full_name):
    """Return (text, remaining). text='' for 404/empty, None to skip."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{full_name}/readme",
        headers={"Authorization": f"Bearer {GH_TOKEN}",
                 "Accept": "application/vnd.github.raw",
                 "User-Agent": "ash-readme-backfill"},
    )
    for attempt in range(4):
        _pace()
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                rem = int(r.headers.get("X-RateLimit-Remaining", "5000"))
                return r.read().decode("utf-8", "replace")[:50000], rem
        except urllib.error.HTTPError as e:
            rem = int(e.headers.get("X-RateLimit-Remaining", "5000"))
            if e.code in (403, 429):
                reset = int(e.headers.get("X-RateLimit-Reset", "0"))
                wait = max(reset - int(time.time()), 5)
                time.sleep(min(wait + 2, 3600))
                continue
            return "", rem  # 404 etc → store empty
        except Exception:  # noqa: BLE001 — URLError/SSL/timeout: transient
            if attempt == 3:
                return None, 5000
            time.sleep(1.5 * (attempt + 1))
    return None, 5000


def process(full):
    text, rem = fetch_readme(full)
    if text is None:
        return "failed", rem
    for attempt in range(4):
        try:
            with conn().cursor() as cur:
                cur.execute(
                    "UPDATE skills SET readme_content=%s, readme_size=%s "
                    "WHERE repo_full_name=%s", (text, len(text), full))
            return ("empty" if text == "" else "ok"), rem
        except psycopg2.errors.DeadlockDetected:
            time.sleep(0.5 * (attempt + 1))
        except Exception:  # noqa: BLE001 — reset broken connection, retry
            _local.conn = None
            time.sleep(0.5 * (attempt + 1))
    return "failed", rem


def main():
    cap = int(sys.argv[1]) if len(sys.argv) > 1 else 999999
    c = psycopg2.connect(DB_URL)
    cur = c.cursor()
    cur.execute(
        "SELECT repo_full_name FROM skills "
        "WHERE stars >= 5 AND readme_content IS NULL "
        "ORDER BY score DESC NULLS LAST LIMIT %s", (cap,))
    targets = [r[0] for r in cur.fetchall()]
    cur.close(); c.close()
    print(f"targets: {len(targets)} skills · {WORKERS} workers · ≤{1/MIN_INTERVAL:.1f}/s", flush=True)

    n = ok = empty = failed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(process, f): f for f in targets}
        for fut in as_completed(futs):
            status, rem = fut.result()
            n += 1
            ok += status == "ok"; empty += status == "empty"; failed += status == "failed"
            if n % 50 == 0:
                rate = n / max(time.time() - t0, 1)
                eta = int((len(targets) - n) / max(rate, 0.01) / 60)
                print(f"  [{n}/{len(targets)}] ok={ok} empty404={empty} failed={failed} "
                      f"gh={rem} · {rate:.1f}/s · ETA {eta}m", flush=True)
    print(f"\n✓ done: ok={ok} empty404={empty} failed={failed}", flush=True)


if __name__ == "__main__":
    main()
