"""Liveness probe for catalog entries — find repos that 404 on GitHub.

Why this exists (2026-08-05): `/skill/Manavarya09/design-extract/` (3,334★) sat
in the catalog for six weeks pointing at a deleted repo. Incremental sync only
re-fetches repos with `pushed:>LAST_SYNC`, so a repo that is DELETED is
indistinguishable from one that is merely quiet — it just stops being touched
and lingers forever with a dead GitHub link. Nothing in the pipeline ever asks
"does this still exist?".

Read-only: prints a report, writes ops/output/dead-repos.json. It never mutates
the DB — removal is a separate, reviewed step.

Run: python ops/probe_dead_repos.py --min-stars 500 [--limit N]
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import psycopg2
import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "output")
STALE_DAYS = 30
# Everything here goes through the local Clash proxy (7897). A single shared
# Session at 8 workers made all 895 probes fail with connection errors — the
# proxy drops pooled connections under that fan-out. Per-thread sessions at 4
# workers + retries is the combination that actually completes.
WORKERS = 4
TIMEOUT = 20
RETRIES = 3
_local = threading.local()


def github_token():
    """Resolve a token that actually works, and fail loudly if none does.

    Two traps, both hit on 2026-08-05: (1) backend/.env carries an EXPIRED
    GITHUB_TOKEN, and load_dotenv() pushes it into os.environ; (2) `gh auth
    token` honours GH_TOKEN/GITHUB_TOKEN from the environment, so once (1)
    happens even the CLI echoes the dead token back. The result was 895 probes
    silently returning 401 and being tallied as "inconclusive" — a broken run
    that looked like a clean bill of health. So: strip the env override before
    asking gh, and verify against /rate_limit before probing anything.
    """
    clean_env = {k: v for k, v in os.environ.items()
                 if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
    candidates = [
        ("gh auth token", subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True,
            env=clean_env).stdout.strip()),
        ("GITHUB_TOKEN env", os.environ.get("GITHUB_TOKEN", "")),
    ]
    for label, tok in candidates:
        if not tok:
            continue
        # Retry: the local proxy drops connections intermittently, and a
        # transient blip here used to abort the whole run before probing
        # anything. Only a real HTTP rejection should disqualify a token.
        for attempt in range(RETRIES):
            try:
                r = requests.get("https://api.github.com/rate_limit",
                                 headers={"Authorization": f"Bearer {tok}"},
                                 timeout=TIMEOUT)
            except requests.RequestException as e:
                if attempt == RETRIES - 1:
                    print(f"跳过 {label}:网络不通({type(e).__name__})", file=sys.stderr)
                    break
                time.sleep(2 * (attempt + 1))
                continue
            if r.ok:
                remaining = r.json()["resources"]["core"]["remaining"]
                print(f"使用 {label}(剩余额度 {remaining})", file=sys.stderr)
                return tok
            print(f"跳过 {label}:HTTP {r.status_code}", file=sys.stderr)
            break
    raise SystemExit("没有可用的 GitHub token —— 跑 `gh auth login`,或更新 backend/.env 的 GITHUB_TOKEN")


def fetch_candidates(min_stars, limit, stale_days):
    """Stalest-first, so repeated runs sweep the backlog instead of re-checking
    the same head every time.

    NOTE the floor is applied to a STALE star count, which is the number this
    job exists to correct — so it can exclude exactly the rows that need it
    most. s1dashu/ip-as-logo-skill sat at 46 in the database while GitHub showed
    562: a 12x understatement, permanently invisible to a >=50 filter, and
    therefore permanently below MIN_STARS_FOR_PAGE with no page generated for a
    562-star repo. 3,537 rows were in that trap on 2026-08-18.

    Callers should keep min_stars well under the page threshold (the workflow
    uses 20 against a threshold of 50) so repos climbing toward it are swept in
    rather than locked out by the very number that is wrong."""
    load_dotenv(os.path.join(ROOT, "..", "backend", ".env"))
    conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"], connect_timeout=20)
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT repo_full_name, stars, last_synced
                FROM skills
                WHERE last_synced < now() - make_interval(days => %s)
                  AND stars >= %s
                  AND repo_status <> 'gone'
                ORDER BY last_synced ASC
                LIMIT %s""",
            (stale_days, min_stars, limit),
        )
        return cur.fetchall()
    finally:
        conn.close()


def session_for_thread(token):
    s = getattr(_local, "session", None)
    if s is None:
        s = requests.Session()
        s.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        })
        _local.session = s
    return s


def write_status(results):
    """Persist probe verdicts to skills.repo_status.

    Only ever writes rows this run actually probed, and never writes 'live' over
    a row it failed to reach — an inconclusive probe becomes 'unknown', so a
    proxy outage can't silently launder dead repos back into the live catalog.
    """
    load_dotenv(os.path.join(ROOT, "..", "backend", ".env"))
    conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"], connect_timeout=30)
    try:
        cur = conn.cursor()
        for status, names in results.items():
            if not names:
                continue
            cur.execute(
                """UPDATE skills
                   SET repo_status = %s, repo_status_checked_at = now()
                   WHERE repo_full_name = ANY(%s)""",
                (status, names),
            )
            print(f"  {status}: {cur.rowcount} 行", file=sys.stderr)
        conn.commit()
    finally:
        conn.close()


def write_stats(rows):
    """Refresh stars/forks/last_commit from the probe payloads.

    prev_stars is only moved when the value actually changed, so star_velocity
    (computed as stars - prev_stars) still reflects a real delta rather than
    being zeroed by every no-op refresh.
    """
    if not rows:
        return
    load_dotenv(os.path.join(ROOT, "..", "backend", ".env"))
    conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"], connect_timeout=30)
    try:
        cur = conn.cursor()
        changed = 0
        for name, stars, forks, issues, pushed in rows:
            cur.execute(
                """UPDATE skills
                   SET prev_stars = CASE WHEN stars <> %s THEN stars ELSE prev_stars END,
                       stars = %s, forks = %s, open_issues = %s,
                       last_commit_at = %s, last_synced = now()
                   WHERE repo_full_name = %s AND stars IS DISTINCT FROM %s""",
                (stars, stars, forks, issues, pushed, name, stars),
            )
            changed += cur.rowcount
        conn.commit()
        print(f"  刷新 star 变化的行: {changed}/{len(rows)}", file=sys.stderr)
    finally:
        conn.close()


def probe(token, row):
    """Return (row, status, payload). 404 = gone, 200 = alive, None = unknown.

    The 200 response already carries stars/forks/pushed_at, so the liveness
    probe doubles as a data refresh at zero extra quota. That matters because
    sync CANNOT refresh these rows: it discovers repos via search with a
    `pushed:>LAST_SYNC` filter, so a repo that stops being pushed is never
    re-fetched and its star count freezes forever. mattpocock/skills sat at
    173,857 while GitHub showed 210,101 — a 21% understatement on a top-3
    repo, frozen since 2026-07-16. 56% of the repos we generate pages for were
    14+ days stale.
    """
    name = row[0]
    s = session_for_thread(token)
    for attempt in range(RETRIES):
        try:
            r = s.get(f"https://api.github.com/repos/{name}", timeout=TIMEOUT)
            return row, r.status_code, (r.json() if r.status_code == 200 else None)
        except requests.RequestException:
            _local.session = None
            s = session_for_thread(token)
            time.sleep(1 + attempt)
    return row, None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-stars", type=int, default=500)
    ap.add_argument("--limit", type=int, default=1000)
    ap.add_argument("--stale-days", type=int, default=STALE_DAYS)
    ap.add_argument("--write", action="store_true",
                    help="persist verdicts to skills.repo_status (default: report only)")
    ap.add_argument("--apply-from-json", action="store_true",
                    help="skip probing; replay the last run's verdicts into the DB")
    args = ap.parse_args()

    if args.apply_from_json:
        with open(os.path.join(OUT_DIR, "repo-status-buckets.json")) as f:
            write_status(json.load(f))
        return

    rows = fetch_candidates(args.min_stars, args.limit, args.stale_days)
    print(f"探测 {len(rows)} 个候选(stars>={args.min_stars},{args.stale_days}天+未同步)…", file=sys.stderr)

    token = github_token()
    dead, alive, unknown = [], 0, 0
    buckets = {"gone": [], "live": [], "unknown": []}
    fresh = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for row, status, payload in pool.map(lambda r: probe(token, r), rows):
            if payload:
                fresh.append((payload["full_name"], payload["stargazers_count"],
                              payload.get("forks_count") or 0,
                              payload.get("open_issues_count") or 0,
                              payload.get("pushed_at")))
            name, stars, synced = row
            if status == 404:
                dead.append({"repo_full_name": name, "stars": stars,
                             "last_synced": str(synced)})
                buckets["gone"].append(name)
            elif status == 200:
                alive += 1
                buckets["live"].append(name)
            else:
                unknown += 1
                buckets["unknown"].append(name)

    dead.sort(key=lambda d: -d["stars"])
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "dead-repos.json"), "w") as f:
        json.dump(dead, f, indent=2, ensure_ascii=False)

    print(f"\n死链 {len(dead)} / 存活 {alive} / 不确定 {unknown}")
    if unknown > len(rows) * 0.1:
        print(f"⚠️ 不确定占比 {unknown/len(rows)*100:.0f}% —— 这轮结果不可信(鉴权或网络问题),别当成'没死链'")
    if dead:
        print(f"死链占比 {len(dead)/len(rows)*100:.1f}%,Top 20:")
        for d in dead[:20]:
            print(f"  {d['stars']:>6}★  {d['repo_full_name']}")
    print(f"\n完整名单: ops/output/dead-repos.json")

    # Persist the verdicts BEFORE touching the DB. A transient DNS failure on
    # the write once discarded a completed 4,262-repo sweep, which would have
    # meant re-spending the whole GitHub rate-limit budget to recover it. With
    # the buckets on disk, a failed write is replayable via --apply-from-json.
    buckets_path = os.path.join(OUT_DIR, "repo-status-buckets.json")
    with open(buckets_path, "w") as f:
        json.dump(buckets, f, indent=2, ensure_ascii=False)
    print(f"判定结果: {buckets_path}")

    if args.write:
        print("\n写回 skills.repo_status …", file=sys.stderr)
        write_status(buckets)
        write_stats(fresh)
    else:
        print("(只读模式 —— 加 --write 才会写回数据库)")


if __name__ == "__main__":
    main()
