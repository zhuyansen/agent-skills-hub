#!/usr/bin/env python3
"""Renamed repositories: one catalog row per repository, and a redirect for each old name.

GitHub answers an old repository name with a redirect to the repository it became, and
the clients here follow it without noticing. The sync writes rows under the name GitHub
returns, so the row under the old name was never matched again: on 2026-10-31, 932 rows
with 50+ stars were old names, nearly all marked live, their numbers frozen on the day of the rename
(affaan-m/everything-claude-code at 186,550 stars while affaan-m/ECC had 293,000).

GraphQL's repository(owner, name) resolves an old name to the repository it became, so a
nameWithOwner other than the stored name (ignoring case) marks an old name. A query asks
for BATCH repositories and costs 1 point of the GraphQL budget, which the sync (REST only)
does not use. For each repository found under another name:
  - the new name has a row: the old row is deleted, after the row that stays takes its
    earlier first_seen, its arena votes and its favorites;
  - it does not: the old row is renamed in place (id and first_seen kept), its numbers come
    from GraphQL, and its README and grade are cleared so readme-backfill fetches the new
    README (some repositories became a different project when they were renamed).
skill_redirects (migration 041) records old -> new either way; the build writes a redirect
page at the old /skill/ URL.

Dry run unless --apply. Stops before writing if a sync is queued or running.

Env:  GH_TOKEN; SUPABASE_DB_URL (or backend/.env);
      GITHUB_REPOSITORY + ACTIONS_TOKEN (optional) to see a running sync.
Args: --min-stars N (50)  --repo OWNER/NAME (repeatable)  --minutes N (35)  --apply
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, field

from readme_backfill import Pacer, db_url, summarize, sync_active

GRAPHQL_URL = "https://api.github.com/graphql"
BATCH = 100                 # repositories per query; a query without connections costs 1 point
MIN_INTERVAL = 1.0          # seconds between queries
HTTP_TIMEOUT = 60
RETRIES = 3
BACKOFF = 5                 # seconds, times the attempt number
GRAPHQL_FLOOR = 200         # points of the hour's GraphQL budget to leave
MAX_ERRORS = 3 * BATCH      # failed lookups after which GitHub is having trouble: stop
REFUSED = (401, 403, 429)   # token rejected or rate-limited: stop rather than retry
DEFAULT_MIN_STARS = 50      # the rows with a page (MIN_STARS_FOR_PAGE in the frontend)
DEFAULT_MINUTES = 35        # sweep budget; the Actions job is killed at 45
SYNC_CHECK_EVERY = 25       # repositories written between running-sync checks
DESCRIPTION_MAX = 500       # what data_cleaner keeps
ERROR_SHARE = 10            # a run fails when more than 1 in this many lookups failed,
MIN_ERRORS = 10             # and more than this many
USER_AGENT = "agentskillshub-renamed-repos"
NODE_FIELDS = "nameWithOwner url description stargazerCount forkCount pushedAt owner { avatarUrl }"

TIMEOUT_SQL = "SET LOCAL statement_timeout = '60s'"
CANDIDATE_SQL = "SELECT id, repo_full_name, stars FROM skills WHERE stars >= %(min_stars)s ORDER BY stars DESC"
NAMED_SQL = "SELECT id, repo_full_name, stars FROM skills WHERE repo_full_name = ANY(%(names)s)"
CURRENT_SQL = "SELECT id, repo_full_name, stars FROM skills WHERE lower(repo_full_name) = ANY(%(names)s)"
RENAME_SQL = (
    "UPDATE skills SET repo_full_name = %(name)s, repo_name = %(repo)s, repo_url = %(url)s, "
    "author_name = %(owner)s, author_avatar_url = %(avatar)s, description = %(description)s, "
    # prev_stars too: the jump from the frozen count is not one day's gain.
    "stars = %(stars)s, prev_stars = %(stars)s, forks = %(forks)s, "
    "pushed_at = %(pushed)s, last_commit_at = %(pushed)s, "
    "readme_content = NULL, readme_size = 0, readme_fetched_at = NULL, "
    "security_grade = 'unknown', security_flags = '[]', "
    "repo_status = 'live', repo_status_checked_at = now(), last_synced = now() "
    "WHERE id = %(id)s"
)
# Votes move to the row that stays, except one its voter already cast for that row the
# same day (arena_votes_daily_unique); those go with the old row.
VOTE_MOVE_SQL = (
    "UPDATE arena_votes v SET {side} = %(keep)s WHERE v.{side} = %(old)s AND NOT EXISTS ("
    "SELECT 1 FROM arena_votes d WHERE d.voter_hash = v.voter_hash "
    "AND d.scenario_tag = v.scenario_tag AND d.vote_date = v.vote_date "
    "AND d.pair_low = LEAST(%(keep)s, v.{other}) AND d.pair_high = GREATEST(%(keep)s, v.{other}))"
)
MERGE_SQL = (
    # The repository has been in the catalog since the old row's first_seen.
    "UPDATE skills n SET first_seen = o.first_seen FROM skills o "
    "WHERE n.id = %(keep)s AND o.id = %(old)s AND o.first_seen < n.first_seen",
    # A vote between two rows of one repository compares nothing.
    "DELETE FROM arena_votes WHERE (winner_id = %(old)s AND loser_id = %(keep)s) "
    "OR (winner_id = %(keep)s AND loser_id = %(old)s)",
    VOTE_MOVE_SQL.format(side="winner_id", other="loser_id"),
    VOTE_MOVE_SQL.format(side="loser_id", other="winner_id"),
    # Favorites too, unless the user saved the row that stays as well (UNIQUE (user_id, skill_id)).
    "UPDATE user_favorites f SET skill_id = %(keep)s WHERE f.skill_id = %(old)s AND NOT EXISTS ("
    "SELECT 1 FROM user_favorites d WHERE d.user_id = f.user_id AND d.skill_id = %(keep)s)",
    # No foreign key here; the sync computes the row that stays its own.
    "DELETE FROM skill_compositions WHERE skill_id = %(old)s OR compatible_skill_id = %(old)s",
    "DELETE FROM skills WHERE id = %(old)s",
)
REDIRECT_SQL = (
    "INSERT INTO skill_redirects (old_full_name, new_full_name) VALUES (%(old)s, %(new)s) "
    "ON CONFLICT (old_full_name) DO UPDATE SET new_full_name = EXCLUDED.new_full_name",
    # Earlier old names of this repository now point at its current name.
    "UPDATE skill_redirects SET new_full_name = %(new)s WHERE lower(new_full_name) = lower(%(old)s)",
)
# A name that has a row again is no longer an old name.
LIVE_NAME_SQL = "DELETE FROM skill_redirects WHERE lower(old_full_name) = lower(%(new)s)"


@dataclass(frozen=True)
class Row:
    id: int
    full_name: str
    stars: int


@dataclass(frozen=True)
class Found:
    """A repository as GraphQL answers for a catalog row's name."""
    full_name: str
    url: str
    description: str
    stars: int
    forks: int
    pushed_at: str | None
    avatar: str


@dataclass
class Move:
    """One repository found under another name: its old rows (most stars first) and the
    catalog's row under the new name, if there is one."""
    found: Found
    old: list[Row] = field(default_factory=list)
    keep: Row | None = None

    @property
    def target(self) -> str:
        """The name the redirects point at: the existing row's spelling, else GitHub's."""
        return self.keep.full_name if self.keep else self.found.full_name


# ── GraphQL ───────────────────────────────────────────────────────────────────────────

def graphql_query(names: list[str]) -> str:
    """One aliased repository() lookup per name (r0, r1, ...), and the budget left."""
    parts = []
    for i, name in enumerate(names):
        owner, _, repo = name.partition("/")
        parts.append(f"r{i}: repository(owner: {json.dumps(owner)}, name: {json.dumps(repo)}) "
                     f"{{ {NODE_FIELDS} }}")
    return "query { " + " ".join(parts) + " rateLimit { remaining } }"


class Halt(Exception):
    """GitHub refused the token or rate-limited it: stop looking things up."""


def fetch_once(req: urllib.request.Request) -> dict | None:
    """The response body, or None for an answer worth retrying."""
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            body = json.load(r)
    except urllib.error.HTTPError as exc:
        if exc.code in REFUSED:
            raise Halt(f"GitHub answered HTTP {exc.code}") from exc
        print(f"  GraphQL: HTTP {exc.code}", flush=True)
        return None
    except (OSError, http.client.HTTPException, ValueError) as exc:
        print(f"  GraphQL: {type(exc).__name__}: {exc}", flush=True)
        return None
    if any(e.get("type") == "RATE_LIMITED" for e in body.get("errors", [])):
        raise Halt("GraphQL rate limit reached")
    return body


def post_graphql(query: str, token: str, pacer: Pacer) -> dict | None:
    """The response body when it carries data, else None after RETRIES attempts."""
    req = urllib.request.Request(GRAPHQL_URL, data=json.dumps({"query": query}).encode(), headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": USER_AGENT})
    for attempt in range(1, RETRIES + 1):
        pacer.wait()
        body = fetch_once(req)
        if body and body.get("data"):
            return body
        if body:
            print(f"  GraphQL attempt {attempt}: {str(body.get('errors'))[:200]}", flush=True)
        time.sleep(BACKOFF * attempt)
    return None


def to_found(node: dict) -> Found:
    name = node["nameWithOwner"]
    return Found(
        full_name=name, url=node.get("url") or f"https://github.com/{name}",
        description=(node.get("description") or "").strip()[:DESCRIPTION_MAX],
        stars=node.get("stargazerCount") or 0, forks=node.get("forkCount") or 0,
        pushed_at=node.get("pushedAt"), avatar=(node.get("owner") or {}).get("avatarUrl") or "",
    )


def verdict(stored: str, answered: str) -> str:
    """'same', 'case' (GitHub serves both spellings, so not an old name) or 'renamed'."""
    if answered == stored:
        return "same"
    return "case" if answered.lower() == stored.lower() else "renamed"


def read_batch(body: dict | None, rows: list[Row]) -> list[tuple[Row, str, Found | None]]:
    """(row, verdict, found) per row; verdict is also 'absent' (NOT_FOUND) or 'error'."""
    if body is None:
        return [(row, "error", None) for row in rows]
    data = body.get("data") or {}
    failed = {e["path"][0]: e.get("type", "") for e in body.get("errors", []) if e.get("path")}
    out = []
    for i, row in enumerate(rows):
        node = data.get(f"r{i}")
        if node is None:
            out.append((row, "absent" if failed.get(f"r{i}") == "NOT_FOUND" else "error", None))
        else:
            found = to_found(node)
            out.append((row, verdict(row.full_name, found.full_name), found))
    return out


def budget_left(body: dict | None) -> int:
    return ((body or {}).get("data") or {}).get("rateLimit", {}).get("remaining", GRAPHQL_FLOOR)


@dataclass
class Sweep:
    renamed: list[tuple[Row, Found]] = field(default_factory=list)  # old rows, with what each became
    counts: Counter = field(default_factory=Counter)                 # verdicts
    stopped: str = ""                                                # why it ended early, or ''
    refused: bool = False                                            # by GitHub (token, rate limit)


def tally(sw: Sweep, results: list[tuple[Row, str, Found | None]]) -> None:
    for row, kind, found in results:
        sw.counts[kind] += 1
        if kind == "renamed":
            sw.renamed.append((row, found))


def stop_reason(sw: Sweep, deadline: float, minutes: float) -> str:
    if time.monotonic() > deadline:
        return f"time budget ({minutes:g} min) used"
    return f"{sw.counts['error']} lookups failed" if sw.counts["error"] >= MAX_ERRORS else ""


def sweep(rows: list[Row], token: str, minutes: float) -> Sweep:
    """Looks every row up, BATCH at a time, until the end, the time budget or a refusal."""
    sw, pacer, deadline = Sweep(), Pacer(MIN_INTERVAL), time.monotonic() + minutes * 60
    for start in range(0, len(rows), BATCH):
        sw.stopped = stop_reason(sw, deadline, minutes)
        if sw.stopped:
            return sw
        batch = rows[start:start + BATCH]
        try:
            body = post_graphql(graphql_query([r.full_name for r in batch]), token, pacer)
        except Halt as exc:
            sw.stopped, sw.refused = str(exc), True
            return sw
        tally(sw, read_batch(body, batch))
        if budget_left(body) < GRAPHQL_FLOOR:
            sw.stopped = "GraphQL budget under the floor"
            return sw
    return sw


# ── what to do ────────────────────────────────────────────────────────────────────────

def plan(renamed: list[tuple[Row, Found]], current: dict[str, Row]) -> list[Move]:
    """One Move per repository, most-starred old row first. `current`: catalog rows by
    lowercased name, looked up for the new names."""
    moves: dict[str, Move] = {}
    for row, found in renamed:
        moves.setdefault(found.full_name.lower(), Move(found)).old.append(row)
    for key, move in moves.items():
        move.old.sort(key=lambda r: -r.stars)
        move.keep = current.get(key)
    return sorted(moves.values(), key=lambda m: -m.old[0].stars)


def describe(move: Move) -> list[str]:
    """Report lines: one per old row, saying whether it is renamed in place or deleted."""
    where = f"{move.keep.stars:,} stars in the catalog" if move.keep else "not in the catalog"
    lines = []
    for i, row in enumerate(move.old):
        action = "rename" if move.keep is None and i == 0 else "delete"
        lines.append(f"  {action:<6} {row.stars:>8,}  {row.full_name} -> {move.target} "
                     f"({where}; {move.found.stars:,} on GitHub)")
    return lines


def rename_params(row: Row, found: Found) -> dict:
    owner, _, repo = found.full_name.partition("/")
    return {"id": row.id, "name": found.full_name, "repo": repo, "url": found.url, "owner": owner,
            "avatar": found.avatar, "description": found.description, "stars": found.stars,
            "forks": found.forks, "pushed": found.pushed_at}


def statements(move: Move) -> list[tuple[str, dict]]:
    """Every write for one repository, in order: rename (when the new name has no row),
    merge each other old row into the row that stays, then the redirects."""
    keep, merged, steps = move.keep, move.old, []
    if keep is None:
        keep, merged = move.old[0], move.old[1:]
        steps.append((RENAME_SQL, rename_params(keep, move.found)))
    steps += [(sql, {"keep": keep.id, "old": row.id}) for row in merged for sql in MERGE_SQL]
    steps.append((LIVE_NAME_SQL, {"new": move.target}))
    steps += [(sql, {"old": row.full_name, "new": move.target}) for row in move.old for sql in REDIRECT_SQL]
    return steps


# ── database ──────────────────────────────────────────────────────────────────────────

def read(conn, sql: str, params: dict) -> list[Row]:
    with conn.cursor() as cur:
        cur.execute(TIMEOUT_SQL)
        cur.execute(sql, params)
        rows = [Row(*r) for r in cur.fetchall()]
    conn.rollback()
    return rows


def candidates(conn, min_stars: int, names: list[str] | None) -> list[Row]:
    if names:
        rows = read(conn, NAMED_SQL, {"names": names})
    else:
        rows = read(conn, CANDIDATE_SQL, {"min_stars": min_stars})
    return [r for r in rows if r.full_name.count("/") == 1]


def current_rows(conn, renamed: list[tuple[Row, Found]]) -> dict[str, Row]:
    """Catalog rows under the new names, by lowercased name."""
    names = sorted({found.full_name.lower() for _, found in renamed})
    if not names:
        return {}
    return {r.full_name.lower(): r for r in read(conn, CURRENT_SQL, {"names": names})}


def write(conn, move: Move) -> None:
    """One transaction per repository: all of its writes or none."""
    try:
        with conn.cursor() as cur:
            cur.execute(TIMEOUT_SQL)
            for sql, params in statements(move):
                cur.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def apply(conn, moves: list[Move]) -> tuple[Counter, str]:
    """Rows renamed and deleted, failures; stops before a write if a sync is queued or running."""
    done = Counter()
    for i, move in enumerate(moves):
        if i % SYNC_CHECK_EVERY == 0 and sync_active():
            return done, "a sync is queued or running"
        try:
            write(conn, move)
        except Exception as exc:  # noqa: BLE001 — report it, go on with the next repository
            done["failed"] += 1
            print(f"  failed {move.old[0].full_name}: {exc}", flush=True)
            continue
        renamed_in_place = int(move.keep is None)
        done["renamed"] += renamed_in_place
        done["deleted"] += len(move.old) - renamed_in_place
    return done, ""


# ── run ───────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-stars", type=int, default=DEFAULT_MIN_STARS)
    ap.add_argument("--repo", action="append", help="check this catalog row only (repeatable)")
    ap.add_argument("--minutes", type=float, default=DEFAULT_MINUTES, help="time budget for the lookups")
    ap.add_argument("--apply", action="store_true", help="write; without it, only report")
    return ap.parse_args()


def report(args: argparse.Namespace, rows: list[Row], sw: Sweep, moves: list[Move],
           done: Counter, halted: str) -> None:
    olds, lone, counts = sum(len(m.old) for m in moves), sum(m.keep is None for m in moves), sw.counts
    stopped = sw.stopped or halted
    summarize([
        "## Renamed repositories" + ("" if args.apply else " (dry run)"),
        f"- rows looked up: {sum(counts.values())} of {len(rows)} (>= {args.min_stars} stars) · "
        f"old names: {olds} of {len(moves)} repositories ({len(moves) - lone} with a row under the new "
        f"name, {lone} without) · spelled in another case: {counts['case']} · not found: "
        f"{counts['absent']} · lookups failed: {counts['error']}",
        f"- written: {done['renamed']} renamed, {done['deleted']} deleted, {done['failed']} failed"
        if args.apply else "- nothing written (pass --apply)",
        f"- stopped early: {stopped}" if stopped else "- ran to the end",
    ])


def exit_code(rows: list[Row], sw: Sweep, done: Counter) -> int:
    """1 when GitHub refused us, a write failed, or too many lookups did."""
    too_many = sw.counts["error"] > max(MIN_ERRORS, len(rows) // ERROR_SHARE)
    return 1 if sw.refused or done["failed"] or too_many else 0


def main() -> int:
    import psycopg2
    args = parse_args()
    conn = psycopg2.connect(db_url(), connect_timeout=30)
    rows = candidates(conn, args.min_stars, args.repo)
    print(f"rows: {len(rows)} (>= {args.min_stars} stars)", flush=True)
    sw = sweep(rows, os.environ["GH_TOKEN"].strip(), args.minutes)
    moves = plan(sw.renamed, current_rows(conn, sw.renamed))
    for move in moves:
        print("\n".join(describe(move)), flush=True)
    done, halted = apply(conn, moves) if args.apply else (Counter(), "")
    conn.close()
    report(args, rows, sw, moves, done, halted)
    return exit_code(rows, sw, done)


if __name__ == "__main__":
    sys.exit(main())
