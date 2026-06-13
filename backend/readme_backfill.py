#!/usr/bin/env python3
"""
README backfill — fetch missing READMEs for quality skills (stars>=5) so the
existing SecurityScanner can grade them, driving down the ~99% `unknown` rate.

The sync's Phase 5 only fetches 1000/run (was 300) and only for repos in the
current sync set, so coverage of the quality subset crawls. This is a one-shot
backfill: pull every stars>=5 skill with no README, fetch it from GitHub, and
write readme_content/readme_size back. Resume-able (only touches NULL readme),
rate-limit aware, idempotent.

Env:
    GH_TOKEN          a valid GitHub token (e.g. `gh auth token`) — 5000/hr
    SUPABASE_DB_URL   from backend/.env (writes readme_content)
Args:
    [max_count]       cap this run (default 999999); pass e.g. 200 to validate.

A 404 (no README on the repo) writes "" so it isn't retried and the scanner
correctly leaves it ungraded.
"""

import os
import re
import sys
import time
import urllib.request

import psycopg2

GH_TOKEN = os.environ["GH_TOKEN"].strip()


def db_url():
    for line in open(os.path.join(os.path.dirname(__file__), ".env")):
        m = re.match(r'\s*SUPABASE_DB_URL\s*=\s*["\']?([^"\'\n]+)', line)
        if m:
            return m.group(1).strip()
    return os.environ["SUPABASE_DB_URL"]


def fetch_readme(full_name):
    """Return (text, status). text is "" for 404/empty."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{full_name}/readme",
        headers={"Authorization": f"Bearer {GH_TOKEN}",
                 "Accept": "application/vnd.github.raw",
                 "User-Agent": "ash-readme-backfill"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            remaining = int(r.headers.get("X-RateLimit-Remaining", "5000"))
            return r.read().decode("utf-8", "replace")[:50000], 200, remaining
    except urllib.error.HTTPError as e:
        remaining = int(e.headers.get("X-RateLimit-Remaining", "5000"))
        reset = int(e.headers.get("X-RateLimit-Reset", "0"))
        if e.code in (403, 429):
            wait = max(reset - int(time.time()), 1)
            print(f"  ⏳ rate-limited, sleeping {wait}s", flush=True)
            time.sleep(min(wait + 2, 3600))
            return None, e.code, 0
        return "", e.code, remaining  # 404 etc → store empty, skip future


def main():
    cap = int(sys.argv[1]) if len(sys.argv) > 1 else 999999
    conn = psycopg2.connect(db_url())
    # Autocommit + single-row updates: locks are held for microseconds, so the
    # backfill can't deadlock with a concurrent sync writing the same table.
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(
        "SELECT repo_full_name FROM skills "
        "WHERE stars >= 5 AND readme_content IS NULL "
        "ORDER BY score DESC NULLS LAST LIMIT %s",
        (cap,),
    )
    targets = [r[0] for r in cur.fetchall()]
    print(f"targets: {len(targets)} skills (stars>=5, no README)", flush=True)

    def write(full, text):
        for attempt in range(4):
            try:
                cur.execute(
                    "UPDATE skills SET readme_content=%s, readme_size=%s "
                    "WHERE repo_full_name=%s",
                    (text, len(text), full),
                )
                return True
            except psycopg2.errors.DeadlockDetected:
                time.sleep(0.5 * (attempt + 1))
        return False

    done = empty = failed = 0
    for i, full in enumerate(targets, 1):
        text, status, remaining = fetch_readme(full)
        if text is None:  # rate-limited, retry same repo once
            text, status, remaining = fetch_readme(full)
        if text is None or not write(full, text):
            failed += 1
            continue
        if text == "":
            empty += 1
        else:
            done += 1
        if i % 25 == 0:
            print(f"  [{i}/{len(targets)}] fetched={done} empty404={empty} "
                  f"failed={failed} gh_remaining={remaining}", flush=True)
        if remaining < 50:
            print("  ⏳ low rate budget, sleeping 60s", flush=True)
            time.sleep(60)
        time.sleep(0.4)
    cur.close()
    conn.close()
    print(f"\n✓ done: fetched={done} empty404={empty} failed={failed}", flush=True)


if __name__ == "__main__":
    main()
