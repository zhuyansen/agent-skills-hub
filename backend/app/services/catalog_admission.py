"""Who gets into the catalog without a person looking, and how the rest are recorded.

One rule for three entrances — the weekly coverage scan, submission issues, and
maintainer commands — so they can never disagree. Pure except `apply` and
`decide`, which take a psycopg2 connection.

    approved   >= AUTO_APPROVE_MIN_STARS and a topic word in name or description:
               written active, the next sync fetches it by name
    pending    everything else worth a look: written inactive, listed for a
               /approve or /reject command
    excluded   fork, archived, or a known collision: not written, not listed

Policy decided 2026-09-24 (spec 2026-09-24-catalog-admission-design.md): the
2026-08-20 rule that a search query alone can never pollute the catalog stays
for the long tail; two thresholds together are the automatic door.
"""
from __future__ import annotations

import re
from typing import Literal

AUTO_APPROVE_MIN_STARS = 1000
TOPIC_WORDS = re.compile(r"\b(?:skills?|mcp|agents?|claude|codex|openclaw)\b", re.IGNORECASE)
# Same collisions the scenario pages exclude, plus link lists (they are indexes, not tools).
EXCLUDE = re.compile(r"awesome-|curated list|jevois|jevons", re.IGNORECASE)
REPO_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_REPO_URL = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?=[/\s)>\]#?]|$)")
_COMMAND = re.compile(r"^/(approve|reject)\s+(\S+)\s*$")

Verdict = Literal["approved", "pending", "excluded"]

SOURCE_AUTO = "coverage-auto"
SOURCE_PENDING = "coverage-pending"

# Only a pending row can be rewritten: a decision (approved/rejected) is never undone by
# a re-submission or a later scan. Returns the row's status after the statement.
UPSERT_SQL = (
    "INSERT INTO extra_repos (full_name, is_active, status, submitted_by) "
    "VALUES (%(full_name)s, %(is_active)s, %(status)s, %(submitted_by)s) "
    "ON CONFLICT (full_name) DO UPDATE SET status = EXCLUDED.status, "
    "is_active = EXCLUDED.is_active, submitted_by = EXCLUDED.submitted_by, reviewed_at = now() "
    "WHERE extra_repos.status = 'pending' "
    "RETURNING status"
)
STATUS_SQL = "SELECT status FROM extra_repos WHERE full_name = %(full_name)s"


def on_topic(repo: dict) -> bool:
    return bool(TOPIC_WORDS.search(f"{repo.get('full_name', '')} {repo.get('description') or ''}"))


def admission(repo: dict) -> Verdict:
    """repo: a GitHub API repository object (full_name, description, stargazers_count, archived, fork)."""
    if repo.get("archived") or repo.get("fork"):
        return "excluded"
    text = f"{repo.get('full_name', '')} {repo.get('description') or ''}"
    if EXCLUDE.search(text):
        return "excluded"
    if (repo.get("stargazers_count") or 0) >= AUTO_APPROVE_MIN_STARS and on_topic(repo):
        return "approved"
    return "pending"


def parse_repo_url(text: str) -> str | None:
    m = _REPO_URL.search(text or "")
    return f"{m.group(1)}/{m.group(2)}" if m else None


def parse_commands(body: str) -> tuple[list[tuple[str, str]], list[str]]:
    """(valid commands, rejected lines). A repo name is untrusted input: only
    owner/repo characters pass, and nothing here is ever interpolated into SQL."""
    good, bad = [], []
    for line in (body or "").splitlines():
        line = line.strip()
        if not line.startswith("/"):
            continue
        m = _COMMAND.match(line)
        if m and REPO_NAME.match(m.group(2)):
            good.append((m.group(1), m.group(2)))
        elif line.startswith(("/approve", "/reject")):
            bad.append(line)
    return good, bad


def apply(conn, full_name: str, verdict: Verdict, submitted_by: str) -> str:
    """Write one verdict. Returns the row's resulting status ('approved' / 'pending' /
    'rejected'), which equals the verdict unless a decided row already existed."""
    if verdict == "excluded":
        return "excluded"
    with conn.cursor() as cur:
        cur.execute(UPSERT_SQL, {"full_name": full_name, "is_active": verdict == "approved",
                                 "status": verdict, "submitted_by": submitted_by})
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(STATUS_SQL, {"full_name": full_name})
        return cur.fetchone()[0]


def decide(conn, full_name: str, decision: str, login: str) -> str:
    """A maintainer's /approve or /reject. Approve inserts when absent; reject only
    touches an existing pending row (nothing to reject otherwise)."""
    with conn.cursor() as cur:
        if decision == "approve":
            cur.execute(
                "INSERT INTO extra_repos (full_name, is_active, status, submitted_by) "
                "VALUES (%(n)s, true, 'approved', %(by)s) "
                "ON CONFLICT (full_name) DO UPDATE SET status = 'approved', is_active = true, "
                "submitted_by = EXCLUDED.submitted_by, reviewed_at = now() "
                "WHERE extra_repos.status = 'pending' RETURNING status",
                {"n": full_name, "by": f"command-{login}"})
        else:
            cur.execute(
                "UPDATE extra_repos SET status = 'rejected', is_active = false, "
                "submitted_by = %(by)s, reviewed_at = now() "
                "WHERE full_name = %(n)s AND status = 'pending' RETURNING status",
                {"n": full_name, "by": f"command-{login}"})
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(STATUS_SQL, {"full_name": full_name})
        row = cur.fetchone()
        return row[0] if row else "absent"
