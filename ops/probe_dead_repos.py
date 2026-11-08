"""Stale-row probe: refresh the catalog rows sync no longer touches, and find repos that are
gone, renamed, or replaced by another repository under the same name.

Why this exists (2026-08-05): `/skill/Manavarya09/design-extract/` (3,334★) sat
in the catalog for six weeks pointing at a deleted repo. Incremental sync only
re-fetches repos with `pushed:>LAST_SYNC`, so a repo that is DELETED is
indistinguishable from one that is merely quiet — it just stops being touched
and lingers forever with a dead GitHub link. Nothing in the pipeline ever asked
"does this still exist?". The same GET /repos/{name} carries fresh stars, so
.github/workflows/refresh-stale.yml runs this three times a day as the refresh for
quiet rows.

The queue (2026-11-08): rows go in order of their last probe, and every row GitHub
answered is stamped (CANDIDATE_SQL, STATUS_SQL). It used to be ordered by last_synced,
which the probe moves only when the star count changed (grade_refresh re-grades a row
whose last_synced moved, so that stays). The ~475 unchanged rows and ~718 old names at
its head came back every run: 98% the same rows on 11-06 and 11-08, while 12,111 rows
went more than 14 days without a refresh.

Same name, another repository (2026-11-08): when a repository is renamed or transferred
and a new one takes its name, GitHub answers that name with the new repository. The probe
copied its stars onto the row and nothing else, so 20 rows held another repository's
numbers or a mix of both (SamurAIGPT/Generative-Media-Skills: 4,337 stars stored, 34 on
GitHub). GitHub keeps created_at through renames and transfers, so a created_at other than
the stored one marks such a row; reset_reused rewrites it and queues it for the next sync.

Without --write it only reports (ops/output/*.json).

Run: python ops/probe_dead_repos.py --min-stars 20 --stale-days 14 [--limit N] [--write]
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import NamedTuple

import psycopg2
import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "output")
BUCKETS_FILE = "repo-status-buckets.json"
RATE_LIMIT_URL = "https://api.github.com/rate_limit"
DEFAULT_MIN_STARS = 500
DEFAULT_LIMIT = 1000
STALE_DAYS = 30
# Everything here goes through the local Clash proxy (7897). A single shared
# Session at 8 workers made all 895 probes fail with connection errors — the
# proxy drops pooled connections under that fan-out. Per-thread sessions at 4
# workers + retries is the combination that actually completes.
WORKERS = 4
TIMEOUT = 20
RETRIES = 3
BACKOFF = 2                 # seconds before a token check's next try, times the attempt number
CONNECT_TIMEOUT = 30
UNKNOWN_WARN_SHARE = 0.1    # more unknown verdicts than this share: the run says nothing about liveness
TOP_DEAD_SHOWN = 20
MOVED_SHOWN = 10
DESCRIPTION_MAX = 500       # what backend/app/services/data_cleaner.py keeps
# extra_repos tag for a reused name. backend/app/services/extra_repo_backfill.py lists it in
# QUEUE_TAGS: the next sync fetches the name and rewrites the whole row, and the queue row is
# retired once the new README is in.
REUSE_TAG = "name-reuse"
# More reused names than this in one run: reset none and fail the run. The 12,111 stale rows
# of 2026-11-08 held 20 in all, so dozens among 1,200 mean the stored created_at is wrong
# somewhere, and a reset would clear the README of rows that are fine.
MAX_REUSED_PER_RUN = 25
_local = threading.local()


class Candidate(NamedTuple):
    id: int
    name: str
    stars: int
    last_synced: datetime | None
    created_at: datetime | None     # GitHub's created_at as the row stored it (naive UTC)


# Due: neither the sync (last_synced) nor this probe (repo_status_checked_at) has looked at
# the row for stale_days. Never-probed rows first, then the longest unprobed.
CANDIDATE_SQL = """
    SELECT id, repo_full_name, stars, last_synced, created_at
      FROM skills
     WHERE stars >= %(min_stars)s
       AND repo_status <> 'gone'
       AND last_synced < now() - make_interval(days => %(days)s)
       AND (repo_status_checked_at IS NULL
            OR repo_status_checked_at < now() - make_interval(days => %(days)s))
     ORDER BY repo_status_checked_at ASC NULLS FIRST, last_synced ASC, id ASC
     LIMIT %(limit)s"""

# Every row GitHub answered is stamped, so it leaves the head of the queue. An unknown row is
# not: it was never reached, and goes first again next run. Its status still drops to
# 'unknown', so a proxy outage can't silently launder dead repos back into the live catalog.
STATUS_SQL = {
    "live": "UPDATE skills SET repo_status = 'live', repo_status_checked_at = now() "
            "WHERE repo_full_name = ANY(%s)",
    "gone": "UPDATE skills SET repo_status = 'gone', repo_status_checked_at = now() "
            "WHERE repo_full_name = ANY(%s)",
    "unknown": "UPDATE skills SET repo_status = 'unknown' WHERE repo_full_name = ANY(%s)",
    # An old name keeps its status: backend/renamed_repos.py merges or renames that row.
    "moved": "UPDATE skills SET repo_status_checked_at = now() WHERE repo_full_name = ANY(%s)",
}

STATS_SQL = """UPDATE skills
       SET prev_stars = CASE WHEN stars <> %s THEN stars ELSE prev_stars END,
           stars = %s, forks = %s, open_issues = %s,
           last_commit_at = %s, last_synced = now()
     WHERE repo_full_name = %s AND stars IS DISTINCT FROM %s"""

# prev_stars too: the drop from the other repository's count is not one day's change.
RESET_SQL = (
    "UPDATE skills SET stars = %(stars)s, prev_stars = %(stars)s, forks = %(forks)s, "
    "open_issues = %(issues)s, created_at = %(created_at)s, pushed_at = %(pushed)s, "
    "last_commit_at = %(pushed)s, description = %(description)s, "
    "readme_content = NULL, readme_size = 0, readme_fetched_at = NULL, "
    "security_grade = 'unknown', security_flags = '[]', "
    "repo_status = 'live', repo_status_checked_at = now(), last_synced = now() "
    "WHERE id = %(id)s"
)
QUEUE_SQL = (
    "INSERT INTO extra_repos (full_name, is_active, status, submitted_by, reviewed_at) "
    "VALUES (%(name)s, true, 'approved', %(tag)s, timezone('utc', now())) "
    "ON CONFLICT (full_name) DO NOTHING"
)


# ── GitHub ────────────────────────────────────────────────────────────────────────────

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
    for label, tok in _token_candidates():
        if tok and _token_ok(label, tok):
            return tok
    raise SystemExit("没有可用的 GitHub token —— 跑 `gh auth login`,或更新 backend/.env 的 GITHUB_TOKEN")


def _token_candidates():
    clean_env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
    gh = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, env=clean_env)
    return [("gh auth token", gh.stdout.strip()), ("GITHUB_TOKEN env", os.environ.get("GITHUB_TOKEN", ""))]


def _token_ok(label, tok):
    """Only a real HTTP rejection disqualifies a token; a network failure skips it too."""
    r, error = _rate_limit(tok)
    if r is None:
        print(f"跳过 {label}:网络不通({error})", file=sys.stderr)
        return False
    if not r.ok:
        print(f"跳过 {label}:HTTP {r.status_code}", file=sys.stderr)
        return False
    print(f"使用 {label}(剩余额度 {r.json()['resources']['core']['remaining']})", file=sys.stderr)
    return True


def _rate_limit(tok):
    """(response, None), or (None, the last error's name) when GitHub never answered. Retried:
    the local proxy drops connections intermittently, and a transient blip here used to abort
    the whole run before probing anything."""
    error = None
    for attempt in range(RETRIES):
        time.sleep(BACKOFF * attempt)
        try:
            return requests.get(RATE_LIMIT_URL, headers={"Authorization": f"Bearer {tok}"},
                                timeout=TIMEOUT), None
        except requests.RequestException as e:
            error = type(e).__name__
    return None, error


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
    s = session_for_thread(token)
    for attempt in range(RETRIES):
        try:
            r = s.get(f"https://api.github.com/repos/{row.name}", timeout=TIMEOUT)
            return row, r.status_code, (r.json() if r.status_code == 200 else None)
        except requests.RequestException:
            _local.session = None
            s = session_for_thread(token)
            time.sleep(1 + attempt)
    return row, None, None


def sweep(token, rows):
    """(row, verdict, payload) per candidate, in candidate order."""
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        answers = list(pool.map(lambda r: probe(token, r), rows))
    return [(row, verdict(row, status, payload), payload) for row, status, payload in answers]


# ── What an answer means ──────────────────────────────────────────────────────────────

def is_old_name(name, payload):
    """True when GitHub answered for a repository under another name: `name` is the old name
    of a renamed or transferred repository, and requests followed the redirect. That row is
    not live under its own name; backend/renamed_repos.py merges or renames it."""
    return bool(payload) and payload.get("full_name", "").lower() != name.lower()


def github_time(value):
    """GitHub's ISO 8601 timestamp as an aware UTC datetime, or None."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def as_utc(value):
    """A stored timestamp as an aware UTC datetime. skills.created_at is timestamp without
    time zone, written in UTC by the sync (data_cleaner parses GitHub's created_at)."""
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def is_reused_name(stored_created_at, payload):
    """True when the repository answering under this name was created at another time than
    the one the row was made from: the original was renamed, transferred or deleted, and a
    new repository took its name. A row without a stored created_at can't be checked and
    counts as the same repository (none in a 100-row sample on 2026-11-08, where all 92
    same-name rows matched GitHub to the second)."""
    stored, answered = as_utc(stored_created_at), github_time((payload or {}).get("created_at"))
    if stored is None or answered is None:
        return False
    return stored.replace(microsecond=0) != answered.replace(microsecond=0)


def verdict(row, status, payload):
    """gone (404), unknown (no answer, or one that isn't a repository), moved (GitHub answered
    for another name), reused (the same name, another repository) or live."""
    if status == 404:
        return "gone"
    if status != 200 or not payload:
        return "unknown"
    if is_old_name(row.name, payload):
        return "moved"
    return "reused" if is_reused_name(row.created_at, payload) else "live"


def stats_rows(results):
    """(name, stars, forks, open issues, pushed_at) to write. A live row under its stored name:
    GitHub's spelling can differ in case, and the UPDATE matches exactly. An old name's answer
    under the new name, which refreshes the row there if the catalog has one. A reused name
    gets none: reset_reused rewrites that row."""
    out = []
    for row, kind, payload in results:
        if kind in ("live", "moved"):
            target = row.name if kind == "live" else payload["full_name"]
            out.append((target, payload["stargazers_count"], payload.get("forks_count") or 0,
                        payload.get("open_issues_count") or 0, payload.get("pushed_at")))
    return out


def buckets_of(results):
    """What --write records and --apply-from-json replays: the stored names per verdict
    (STATUS_SQL) and the star refreshes. Reused names are not in it; see reset_reused."""
    buckets = {kind: [] for kind in STATUS_SQL}
    for row, kind, _ in results:
        if kind in buckets:
            buckets[kind].append(row.name)
    buckets["stats"] = stats_rows(results)
    return buckets


def reused_of(results):
    return [(row, payload) for row, kind, payload in results if kind == "reused"]


# ── Database ──────────────────────────────────────────────────────────────────────────

def connect():
    load_dotenv(os.path.join(ROOT, "..", "backend", ".env"))
    return psycopg2.connect(os.environ["SUPABASE_DB_URL"], connect_timeout=CONNECT_TIMEOUT)


def fetch_candidates(conn, min_stars, limit, stale_days):
    """The rows due for a probe, longest unprobed first, so repeated runs sweep the backlog
    instead of re-checking the same head every time (CANDIDATE_SQL).

    NOTE the floor is applied to a STALE star count, which is the number this
    job exists to correct — so it can exclude exactly the rows that need it
    most. s1dashu/ip-as-logo-skill sat at 46 in the database while GitHub showed
    562: a 12x understatement, permanently invisible to a >=50 filter, and
    therefore permanently below MIN_STARS_FOR_PAGE with no page generated for a
    562-star repo. 3,537 rows were in that trap on 2026-08-18.

    Callers should keep min_stars well under the page threshold (the workflow
    uses 20 against a threshold of 50) so repos climbing toward it are swept in
    rather than locked out by the very number that is wrong."""
    cur = conn.cursor()
    cur.execute(CANDIDATE_SQL, {"min_stars": min_stars, "days": stale_days, "limit": limit})
    return [Candidate(*r) for r in cur.fetchall()]


def write_status(conn, buckets):
    """Persist verdicts to skills.repo_status and repo_status_checked_at (STATUS_SQL). Only
    rows this run probed, by the names the catalog stores."""
    cur = conn.cursor()
    for kind, sql in STATUS_SQL.items():
        names = buckets.get(kind) or []
        if names:
            cur.execute(sql, (names,))
            print(f"  {kind}: {cur.rowcount} 行", file=sys.stderr)
    conn.commit()


def write_stats(conn, rows):
    """Refresh stars/forks/last_commit from the probe payloads.

    prev_stars is only moved when the value actually changed, so star_velocity
    (computed as stars - prev_stars) still reflects a real delta rather than
    being zeroed by every no-op refresh. last_synced moves with it, and only then:
    grade_refresh re-grades a row whose last_synced moved.
    """
    cur = conn.cursor()
    changed = 0
    for name, stars, forks, issues, pushed in rows:
        cur.execute(STATS_SQL, (stars, stars, forks, issues, pushed, name, stars))
        changed += cur.rowcount
    conn.commit()
    print(f"  刷新 star 变化的行: {changed}/{len(rows)}", file=sys.stderr)


def naive_utc(value):
    return value.replace(tzinfo=None) if value else None


def reset_params(row, payload):
    return {
        "id": row.id,
        "stars": payload["stargazers_count"],
        "forks": payload.get("forks_count") or 0,
        "issues": payload.get("open_issues_count") or 0,
        "created_at": naive_utc(github_time(payload.get("created_at"))),
        "pushed": naive_utc(github_time(payload.get("pushed_at"))),
        "description": (payload.get("description") or "").strip()[:DESCRIPTION_MAX],
    }


def reset_reused(conn, reused):
    """Rewrite each reused name's row from GitHub's answer, clear the README and grade it kept
    from the other repository, and queue the name (REUSE_TAG) so the next sync rewrites the
    rest of the row (category, topics, language, score) and fetches the new README; until
    then readme_backfill may fetch it (grade 'unknown', no README). A name already in
    extra_repos is left as it is: an active row is fetched every sync anyway, and an inactive
    one is a decision (rejected) or a finished queue."""
    cur = conn.cursor()
    queued = 0
    for row, payload in reused:
        cur.execute(RESET_SQL, reset_params(row, payload))
        cur.execute(QUEUE_SQL, {"name": row.name, "tag": REUSE_TAG})
        queued += cur.rowcount
    conn.commit()
    print(f"  同名换仓库: 重置 {len(reused)} 行,新排进 extra_repos {queued} 行", file=sys.stderr)


def persist(results, buckets):
    """Write this run's verdicts. Returns the exit code: 1 when the reused names were left
    alone because there were more than MAX_REUSED_PER_RUN."""
    reused = reused_of(results)
    conn = connect()
    try:
        write_status(conn, buckets)
        write_stats(conn, buckets["stats"])
        if len(reused) > MAX_REUSED_PER_RUN:
            print(f"⚠️ 同名换仓库 {len(reused)} 行,超过上限 {MAX_REUSED_PER_RUN}:一行都没重置。"
                  "先查库里的 created_at 是不是整批错了(名单: ops/output/name-reused.json)", file=sys.stderr)
            return 1
        if reused:
            reset_reused(conn, reused)
        return 0
    finally:
        conn.close()


def replay():
    """--apply-from-json: write the last run's statuses, stamps and stars. Reused names are not
    in the file; the next run finds them again."""
    with open(os.path.join(OUT_DIR, BUCKETS_FILE)) as f:
        saved = json.load(f)
    conn = connect()
    try:
        write_status(conn, saved)
        write_stats(conn, [tuple(r) for r in saved.get("stats", [])])
    finally:
        conn.close()
    return 0


# ── Report ────────────────────────────────────────────────────────────────────────────

def reused_entry(row, payload):
    return {"id": row.id, "repo_full_name": row.name,
            "stored_stars": row.stars, "github_stars": payload["stargazers_count"],
            "stored_created_at": str(row.created_at), "github_created_at": payload.get("created_at"),
            "github_id": payload.get("id")}


def save_outputs(results, buckets):
    """dead-repos.json (most stars first), name-reused.json, and the buckets file. Written
    BEFORE touching the DB: a transient DNS failure on the write once discarded a completed
    4,262-repo sweep, which would have meant re-spending the whole GitHub rate-limit budget
    to recover it. With the buckets on disk, a failed write is replayable via --apply-from-json."""
    dead = sorted(({"repo_full_name": r.name, "stars": r.stars, "last_synced": str(r.last_synced)}
                   for r, kind, _ in results if kind == "gone"), key=lambda d: -d["stars"])
    reused = [reused_entry(r, p) for r, p in reused_of(results)]
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, data in (("dead-repos.json", dead), ("name-reused.json", reused), (BUCKETS_FILE, buckets)):
        with open(os.path.join(OUT_DIR, name), "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    return dead, reused


def report(rows, results, dead, reused):
    counts = Counter(kind for _, kind, _ in results)
    print(f"\n死链 {counts['gone']} / 存活 {counts['live']} / 不确定 {counts['unknown']}")
    moved = [row.name for row, kind, _ in results if kind == "moved"]
    if moved:
        print(f"改名仓库的旧名 {len(moved)}(状态不改,交给 backend/renamed_repos.py):{', '.join(moved[:MOVED_SHOWN])}")
    if counts["unknown"] > len(rows) * UNKNOWN_WARN_SHARE:
        print(f"⚠️ 不确定占比 {counts['unknown']/len(rows)*100:.0f}% —— 这轮结果不可信(鉴权或网络问题),别当成'没死链'")
    report_dead(rows, dead)
    report_reused(reused)
    print("\n完整名单: ops/output/dead-repos.json、ops/output/name-reused.json")
    print(f"判定结果: {os.path.join(OUT_DIR, BUCKETS_FILE)}")


def report_dead(rows, dead):
    if not dead:
        return
    print(f"死链占比 {len(dead)/len(rows)*100:.1f}%,Top {TOP_DEAD_SHOWN}:")
    for d in dead[:TOP_DEAD_SHOWN]:
        print(f"  {d['stars']:>6}★  {d['repo_full_name']}")


def report_reused(reused):
    if not reused:
        return
    print(f"同名换了仓库 {len(reused)} 行(库里的 created_at 和 GitHub 对不上):")
    for e in reused:
        print(f"  {e['repo_full_name']}: 库里 {e['stored_stars']}★ 建于 {e['stored_created_at']},"
              f" GitHub {e['github_stars']}★ 建于 {e['github_created_at']}")


# ── Main ──────────────────────────────────────────────────────────────────────────────

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-stars", type=int, default=DEFAULT_MIN_STARS)
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    ap.add_argument("--stale-days", type=int, default=STALE_DAYS)
    ap.add_argument("--write", action="store_true",
                    help="persist verdicts, stars and reused-name resets (default: report only)")
    ap.add_argument("--apply-from-json", action="store_true",
                    help="skip probing; replay the last run's statuses and stars into the DB")
    return ap.parse_args()


def load_candidates(args):
    conn = connect()
    try:
        rows = fetch_candidates(conn, args.min_stars, args.limit, args.stale_days)
    finally:
        conn.close()
    print(f"探测 {len(rows)} 个候选(stars>={args.min_stars},{args.stale_days}天+未同步也未探测)…",
          file=sys.stderr)
    return rows


def main():
    args = parse_args()
    if args.apply_from_json:
        return replay()
    rows = load_candidates(args)
    results = sweep(github_token(), rows)
    buckets = buckets_of(results)
    dead, reused = save_outputs(results, buckets)
    report(rows, results, dead, reused)
    if not args.write:
        print("(只读模式 —— 加 --write 才会写回数据库)")
        return 0
    print("\n写回 skills …", file=sys.stderr)
    return persist(results, buckets)


if __name__ == "__main__":
    sys.exit(main())
