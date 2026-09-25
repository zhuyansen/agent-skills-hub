#!/usr/bin/env python3
"""README backfill — fetch READMEs for ungraded repos the sync never revisits.

The sync fetches READMEs only for repos its incremental search returned in that
run, so a dormant repo that entered the catalog without one stayed ungraded
forever: on 2026-09-23, 7,711 live repos with >=5 stars and 49,867 with 1-4.
This walks those rows most-starred first and records every definite answer
through app/services/readme_coverage.py, the rule the sync uses too. The next
sync grades what it fetched.

Scheduled by .github/workflows/readme-backfill.yml at 03/11/19 UTC, between
syncs. One request per second globally (4 threads fill latency gaps) and one
autocommit UPDATE per row — the load the instance tolerated in June, when 8
workers alongside an index build made its REST API 504. Stops early when the
GitHub quota the sync shares falls under QUOTA_FLOOR, or a sync is queued or
running.

Env:  GH_TOKEN; SUPABASE_DB_URL (or backend/.env);
      GITHUB_REPOSITORY + ACTIONS_TOKEN (optional) to see a running sync.
Args: --floor N (5)  --cap N (1500)  --allow-floor-drop
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.services.readme_coverage import MISSING_README_SQL

WORKERS = 4
MIN_INTERVAL = 1.0      # seconds between request starts, globally
QUOTA_FLOOR = 1500      # leave this much of the shared token for the next sync
DEFAULT_FLOOR = 5       # first tier: repos someone looks at
LOW_FLOOR = 1           # second tier; 0-star repos are never fetched
DROP_BELOW = 50         # first tier counts as done below this many candidates
CHUNK = 100             # rows between quota / running-sync checks
DEFAULT_CAP = 1500
README_MAX = 50000
HTTP_TIMEOUT = 30
WRITE_FAIL_TOLERANCE = 0.05   # share of attempted rows
WRITE_FAIL_TOLERANCE_MIN = 10

CANDIDATE_SQL = (
    "SELECT repo_full_name FROM skills "
    "WHERE security_grade = 'unknown' AND repo_status IS DISTINCT FROM 'gone' "
    f"AND stars >= %(floor)s AND {MISSING_README_SQL} "
    "ORDER BY stars DESC LIMIT %(cap)s"
)
COUNT_SQL = CANDIDATE_SQL.split(" ORDER BY")[0].replace("SELECT repo_full_name", "SELECT count(*)")
WRITE_SQL = (
    "UPDATE skills SET readme_content = %s, readme_size = %s, readme_fetched_at = now() "
    "WHERE repo_full_name = %s AND (readme_content IS NULL OR readme_content = '')"
)


def clamp_floor(floor: int) -> int:
    return max(floor, LOW_FLOOR)


def choose_floor(first_tier_left: int, allow_drop: bool) -> int:
    return LOW_FLOOR if allow_drop and first_tier_left < DROP_BELOW else DEFAULT_FLOOR


def quota_exhausted(remaining: int) -> bool:
    return remaining < QUOTA_FLOOR


class Pacer:
    def __init__(self, interval: float):
        self.interval, self.lock, self.last = interval, threading.Lock(), 0.0

    def wait(self) -> None:
        with self.lock:
            delay = self.interval - (time.time() - self.last)
            if delay > 0:
                time.sleep(delay)
            self.last = time.time()


def db_url() -> str:
    env_file = Path(__file__).with_name(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            m = re.match(r'\s*SUPABASE_DB_URL\s*=\s*["\']?([^"\'\n]+)', line)
            if m:
                return m.group(1).strip()
    return os.environ["SUPABASE_DB_URL"]


def fetch(full_name: str, token: str, pacer: Pacer) -> tuple[str, str | None, int]:
    """('ok', text, remaining) | ('absent', '', remaining) | ('error', None, remaining).
    urllib follows the 301 GitHub sends for a renamed repo."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{full_name}/readme",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.raw",
                 "User-Agent": "agentskillshub-readme-backfill"})
    pacer.wait()
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            remaining = int(r.headers.get("X-RateLimit-Remaining", "5000"))
            text = r.read().decode("utf-8", "replace")[:README_MAX]
            return ("ok", text, remaining) if text.strip() else ("absent", "", remaining)
    except urllib.error.HTTPError as e:
        remaining = int(e.headers.get("X-RateLimit-Remaining", "5000"))
        if e.code in (403, 429):
            return "error", None, 0  # rate limited: the quota check ends the run
        return ("absent", "", remaining) if e.code == 404 else ("error", None, remaining)
    except Exception:  # noqa: BLE001 — URLError/SSL/timeout: try again next run
        return "error", None, 5000


def sync_active() -> bool:
    """A sync queued or running on this repository (Actions API). False when
    run locally without the Actions env; True when the API can't be read."""
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("ACTIONS_TOKEN")
    if not repo or not token:
        return False
    for status in ("in_progress", "queued"):
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/actions/workflows/sync.yml/runs?status={status}&per_page=1",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
                if json.load(r).get("total_count", 0):
                    return True
        except Exception:  # noqa: BLE001 — can't tell: be safe
            return True
    return False


class Writer:
    """One autocommit connection per thread."""

    def __init__(self, url: str):
        self.url, self.local = url, threading.local()

    def write(self, full_name: str, text: str) -> bool:
        import psycopg2  # imported here so tests need no driver
        for attempt in range(3):
            try:
                conn = getattr(self.local, "conn", None)
                if conn is None:
                    conn = self.local.conn = psycopg2.connect(self.url)
                    conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute(WRITE_SQL, (text, len(text), full_name))
                return True
            except Exception:  # noqa: BLE001 — broken connection: reconnect and retry
                self.local.conn = None
                time.sleep(0.5 * (attempt + 1))
        return False


def candidates(url: str, floor: int, cap: int) -> list[str]:
    import psycopg2
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '60s'")
        cur.execute(CANDIDATE_SQL, {"floor": floor, "cap": cap})
        return [r[0] for r in cur.fetchall()]


def count_first_tier(url: str) -> int:
    import psycopg2
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '60s'")
        cur.execute(COUNT_SQL, {"floor": DEFAULT_FLOOR})
        return cur.fetchone()[0]


def summarize(lines: list[str]) -> None:
    text = "\n".join(lines)
    print(text, flush=True)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as f:
            f.write(text + "\n")


def exit_code(counts: dict) -> int:
    attempted = sum(counts.values())
    return 1 if counts["write_failed"] > max(WRITE_FAIL_TOLERANCE_MIN, attempted * WRITE_FAIL_TOLERANCE) else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--floor", type=int, default=DEFAULT_FLOOR)
    ap.add_argument("--cap", type=int, default=DEFAULT_CAP)
    ap.add_argument("--allow-floor-drop", action="store_true")
    args = ap.parse_args()

    token, url = os.environ["GH_TOKEN"].strip(), db_url()
    floor = clamp_floor(args.floor)
    if args.allow_floor_drop and floor == DEFAULT_FLOOR:
        left = count_first_tier(url)
        floor = choose_floor(left, allow_drop=True)
        print(f"first tier (>= {DEFAULT_FLOOR} stars) left: {left} -> floor {floor}", flush=True)
    targets = candidates(url, floor, args.cap)
    print(f"targets: {len(targets)} (floor {floor}, cap {args.cap}) · {WORKERS} workers · <= {1 / MIN_INTERVAL:.0f}/s",
          flush=True)

    pacer, writer = Pacer(MIN_INTERVAL), Writer(url)
    counts = {"ok": 0, "absent": 0, "error": 0, "write_failed": 0}
    stopped = ""

    def one(full_name: str) -> int:
        status, text, remaining = fetch(full_name, token, pacer)
        if status != "error" and not writer.write(full_name, text or ""):
            status = "write_failed"
        counts[status] += 1
        return remaining

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i in range(0, len(targets), CHUNK):
            if sync_active():
                stopped = "a sync is queued or running"
                break
            lowest = min(pool.map(one, targets[i:i + CHUNK]))
            print(f"  [{min(i + CHUNK, len(targets))}/{len(targets)}] {counts} · quota {lowest}", flush=True)
            if quota_exhausted(lowest):
                stopped = f"GitHub quota {lowest} < {QUOTA_FLOOR}"
                break

    summarize([
        "## README backfill",
        f"- floor: {floor} stars · cap {args.cap} · targets {len(targets)}",
        f"- fetched: {counts['ok']} · no README on GitHub: {counts['absent']} · "
        f"errors (retried next run): {counts['error']} · write failures: {counts['write_failed']}",
        f"- stopped early: {stopped}" if stopped else "- ran to the end of its batch",
    ])
    return exit_code(counts)


if __name__ == "__main__":
    sys.exit(main())
