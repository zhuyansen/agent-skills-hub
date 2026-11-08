"""The live row of every repo a scenario page lists, looked up once per run of the daily pass.

build_video_list.github_row() asks GitHub for a repo's stars, description, creation date, language and
license; daily_video_pass.exclude_gone() asks whether it still exists. The pass ran both for every listed
repo on every page: exclude_gone once, the list builder twice (before and after the thumbnails). That was
14,023 sequential REST calls a run: about 80 minutes, and about 5,000 an hour, the whole quota of the
token. When the quota ran out github_row() slept until it reset, silently, for up to an hour: in the runs
of 11-04..11-07 one to three stalls of 13-22 minutes each, and two runs cut off at the job's 180 minutes.

Now the pass asks once, at the start, about all of them: GraphQL, BATCH repos a request, 1 point a
request (about 45 requests a run). The answers go into a file the whole run shares, the list builder
included (it runs as a child process). Both read it before they ask GitHub anything. A name the file lacks
is still looked up one by one, so a failed batch costs time, not correctness. Without REPO_ROWS_CACHE set
nothing is cached, and a hand run of build_video_list.py works as before.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

CACHE_ENV = "REPO_ROWS_CACHE"   # the run's cache file: JSON lines {"k": lower-case name, "row": row, or null for gone}
BATCH = 100                     # repos per GraphQL request; a request costs 1 point of the 5,000 an hour
ATTEMPTS = 2
RETRY_PAUSE = 5
GONE_SHARE = 0.02               # more "not found" than this share of a run's names is not believed
GONE_FLOOR = 20                 # ... unless it is only this many (a hand run of a few names)
GRAPHQL_TIMEOUT = 120
FRAGMENT = ("fragment F on Repository { nameWithOwner stargazerCount description createdAt "
            "primaryLanguage { name } licenseInfo { spdxId } }")

_seen: dict = {"path": None, "size": -1, "rows": {}}   # the cache file as this process last read it


# ── asking GitHub ─────────────────────────────────────────────────────────────

def row_from_graphql(node: dict) -> dict:
    """The row build_video_list.github_row() makes from the REST answer, made from the GraphQL one.
    A sample of 200 listed repos came out identical in all six fields (11-08)."""
    return {"repo_full_name": node["nameWithOwner"], "stars": node["stargazerCount"], "description": node.get("description"),
            "security_grade": None, "created_at": node.get("createdAt"),
            "language": (node.get("primaryLanguage") or {}).get("name"),
            "license": (node.get("licenseInfo") or {}).get("spdxId")}


def query(names: list[str]) -> str:
    """One aliased lookup per name (owner/repo). json.dumps escapes a name, so it cannot leave its string."""
    fields = []
    for i, name in enumerate(names):
        owner, _, repo = name.partition("/")
        fields.append(f"r{i}: repository(owner: {json.dumps(owner)}, name: {json.dumps(repo)}) {{ ...F }}")
    return "query { " + " ".join(fields) + " } " + FRAGMENT


def parse(names: list[str], text: str) -> dict[str, dict | None]:
    """name -> row, or None where GitHub says "not found" (deleted, or private to the token). A name
    the answer does not settle (an error of another kind, no entry) is left out: it is asked again."""
    try:
        body = json.loads(text)
    except ValueError:
        return {}
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        return {}
    missing = {e["path"][0] for e in body.get("errors") or []
               if isinstance(e, dict) and e.get("type") == "NOT_FOUND" and e.get("path")}
    found: dict[str, dict | None] = {}
    for i, name in enumerate(names):
        node = data.get(f"r{i}")
        if isinstance(node, dict) and node.get("nameWithOwner"):
            found[name] = row_from_graphql(node)
        elif node is None and f"r{i}" in missing:
            found[name] = None
    return found


def run_batch(names: list[str]) -> dict[str, dict | None]:
    """One GraphQL request. gh exits 1 when any name is missing, with the rest of the answer on stdout,
    so stdout is read whatever the exit code is. Raises when the answer settles no name at all."""
    done = subprocess.run(["gh", "api", "graphql", "-f", f"query={query(names)}"],
                          capture_output=True, text=True, timeout=GRAPHQL_TIMEOUT)
    found = parse(names, done.stdout)
    if not found:
        raise RuntimeError(f"GraphQL settled no name: {(done.stderr or done.stdout)[-160:]}")
    return found


def _ask(chunk: list[str], stats: dict) -> dict[str, dict | None]:
    for attempt in range(ATTEMPTS):
        stats["requests"] += 1
        try:
            return run_batch(chunk)
        except (RuntimeError, subprocess.TimeoutExpired):
            if attempt + 1 < ATTEMPTS:
                time.sleep(RETRY_PAUSE)
    return {}


def prefetch(names: list[str]) -> dict:
    """Ask GitHub about every name the cache lacks, BATCH at a time, and remember the answers. Names
    with a folder in them (sub-skill keys) are not repos and are left to the one-by-one lookup."""
    stats = {"asked": 0, "found": 0, "gone": 0, "left": 0, "requests": 0}
    todo, seen = [], set()
    for name in names:
        if name.count("/") != 1 or name.lower() in seen or get(name)[0]:
            continue
        seen.add(name.lower())
        todo.append(name)
    answers: dict[str, dict | None] = {}
    for start in range(0, len(todo), BATCH):
        chunk = todo[start:start + BATCH]
        answers.update(_ask(chunk, stats))
    stats["asked"] = len(todo)
    gone = [name for name, row in answers.items() if row is None]
    if len(gone) > max(GONE_FLOOR, GONE_SHARE * len(todo)):
        # Not 1 repo in 50 vanishing overnight (3 of 4,453 on 11-08): GraphQL is wrong. Believing it would
        # take them off their pages (exclude_gone) and out of the lists. The one-by-one lookup decides.
        stats["doubted"] = len(gone)
        answers = {name: row for name, row in answers.items() if row is not None}
    for name in todo:
        if name not in answers:
            stats["left"] += 1
            continue
        put(name, answers[name])
        stats["gone" if answers[name] is None else "found"] += 1
    return stats


# ── the run's cache file ──────────────────────────────────────────────────────

def cache_file() -> Path | None:
    value = os.environ.get(CACHE_ENV)
    return Path(value) if value else None


def _read(path: Path) -> dict:
    rows: dict = {}
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            rows[record["k"]] = record["row"]
        except (ValueError, KeyError, TypeError):
            continue   # a last line cut short by an interrupted write
    return rows


def _sync() -> dict | None:
    """The cached rows, re-read when the file grew since this process last looked (a child process
    appends to it). None when the run has no cache file."""
    path = cache_file()
    if path is None:
        return None
    if _seen["path"] != path:
        _seen.update(path=path, size=-1, rows={})
    size = path.stat().st_size if path.exists() else 0
    if size != _seen["size"]:
        _seen.update(size=size, rows=_read(path))
    return _seen["rows"]


def get(name: str) -> tuple[bool, dict | None]:
    """(True, row) when the run has looked the repo up; the row is None for one GitHub does not serve."""
    rows = _sync()
    key = name.lower()
    return (True, rows[key]) if rows is not None and key in rows else (False, None)


def put(name: str, row: dict | None) -> None:
    rows = _sync()
    if rows is None:
        return
    rows[name.lower()] = row
    with _seen["path"].open("a", encoding="utf-8") as out:
        out.write(json.dumps({"k": name.lower(), "row": row}, ensure_ascii=False) + "\n")
    _seen["size"] = _seen["path"].stat().st_size
