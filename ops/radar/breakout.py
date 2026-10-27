"""Radar signal ②b: one new repo taking off on its own, anywhere on GitHub.

github_surge (signals.py) needs five owners using one word, so it sees a wave only once
others copy the idea, days after it started. Strata (Niko1221/Strata) was one repo, born
2026-09-24, at 7.7k stars nine days later; its name was being searched from 9/26 while
no second repo carried it. This signal watches the repo itself.

GitHub search, not the catalog: repos created in the last WINDOW_DAYS with at least
MIN_STARS, two pages. A repo breaks out when it averages VELOCITY_MIN stars a day since
birth, or gained DELTA_MIN since yesterday's snapshot. For the new ones the owner's
display name is fetched too, because people search it ("niko strata", not "niko1221").

Repos up to LATE_DAYS old are searched apart, from LATE_MIN_STARS: some take off only
after two weeks (KnifeLemon/Filee, born 2026-09-29, 7.6k stars at three weeks, never
reported). One 30-day search would not do: its two pages started at 856 stars on
2026-10-20 and dropped that day's one-day-old repos at 400-630 stars a day.

A repo stays above the bar for days. It becomes a lead term once, the day it first
breaks out (kept in the snapshot for FLAGGED_DAYS, longer than any repo stays in the
searches). The table shows at most TOP: every first-time breakout, then the fastest of
the others. It used to keep the TOP fastest before asking which were new, so a
first-time breakout below the fifteenth never became a lead (18 of 50 on 2026-10-20).
"""
from __future__ import annotations

import gzip
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

WINDOW_DAYS = 14
MIN_STARS = 300
PAGES = 2
LATE_DAYS = 30         # repos WINDOW_DAYS+1 to LATE_DAYS old: a search of their own
LATE_MIN_STARS = 1000
VELOCITY_MIN = 200     # stars a day since creation
DELTA_MIN = 400        # stars since yesterday's run
TOP = 15
FLAGGED_DAYS = LATE_DAYS + 2
API = "https://api.github.com"


def token() -> str:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        return tok
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _get(path: str, tok: str) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "agentskillshub-radar"}
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    with urllib.request.urlopen(urllib.request.Request(API + path, headers=headers), timeout=30) as res:
        return json.load(res)


def repo_term(name: str) -> str:
    """'universal-modder' -> 'universal modder'; 'OpenDots' -> 'opendots'."""
    return re.sub(r"[-_.]+", " ", name).strip().lower()


def _search(query: str, tok: str) -> list[dict]:
    q = urllib.parse.quote(query)
    repos: list[dict] = []
    for page in range(1, PAGES + 1):
        items = _get(f"/search/repositories?q={q}&sort=stars&order=desc&per_page=100&page={page}", tok).get("items", [])
        repos += items
        if len(items) < 100:
            break
    return repos


def searched(tok: str, today: date) -> tuple[list[dict], int, str | None]:
    """The young repos, then the late ones not among them. A failed late search costs only
    the late repos: (repos, how many are late, the late search's error)."""
    since, late_from, late_to = ((today - timedelta(days=n)).isoformat() for n in (WINDOW_DAYS, LATE_DAYS, WINDOW_DAYS + 1))
    repos = _search(f"created:>={since} stars:>={MIN_STARS}", tok)
    try:
        late = _search(f"created:{late_from}..{late_to} stars:>={LATE_MIN_STARS}", tok)
    except (OSError, ValueError) as e:
        return repos, 0, f"{WINDOW_DAYS + 1}–{LATE_DAYS} 天的仓库没搜到({e})"
    seen = {r["full_name"] for r in repos}
    late = [r for r in late if r["full_name"] not in seen]
    return repos + late, len(late), None


def _speed(row: dict) -> int:
    return -max(row["velocity"], row["delta"] or 0)


def score(repos: list[dict], before: dict[str, int] | None, now: datetime) -> list[dict]:
    """Every repo above the bar, fastest first. `repos` items are GitHub search results."""
    out = []
    for r in repos:
        created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        age = max((now - created).total_seconds() / 86400, 1.0)
        stars = r["stargazers_count"]
        velocity = stars / age
        delta = stars - before[r["full_name"]] if before and r["full_name"] in before else None
        if velocity < VELOCITY_MIN and (delta is None or delta < DELTA_MIN):
            continue
        owner, name = r["full_name"].split("/", 1)
        out.append({"repo": r["full_name"], "owner": owner, "name": name, "stars": stars,
                    "velocity": round(velocity), "delta": delta, "age_days": round(age, 1),
                    "born": created.date().isoformat(), "description": (r.get("description") or "")[:120]})
    return sorted(out, key=_speed)


def shown(rows: list[dict]) -> list[dict]:
    """At most TOP rows, fastest first: the first-time breakouts (the TOP fastest of them),
    then the fastest of those reported before. Rows need "new"."""
    new = [r for r in rows if r["new"]][:TOP]
    return sorted(new + [r for r in rows if not r["new"]][:TOP - len(new)], key=_speed)


def variants(row: dict, display: str) -> list[str]:
    """The ways people end up searching a repo: its name, the owner's handle with it,
    and the owner's display name with it (Strata: 'strata', 'niko1221 strata', 'niko strata')."""
    term = repo_term(row["name"])
    out = [term, f"{row['owner'].lower()} {term}"]
    first = (display or "").split(" ")[0].lower()
    if first and first != row["owner"].lower() and first.isascii() and first.isalpha():
        out.append(f"{first} {term}")
    return out


def mark_new(rows: list[dict], flagged_path: Path, today: date) -> list[dict]:
    """Which rows break out for the first time, then shown(); the rows shown are remembered.
    A first-time breakout left out today stays new for tomorrow."""
    flagged: dict[str, str] = json.loads(gzip.decompress(flagged_path.read_bytes())) if flagged_path.exists() else {}
    for row in rows:
        row["new"] = row["repo"] not in flagged
    rows = shown(rows)
    for row in rows:
        flagged.setdefault(row["repo"], today.isoformat())
    cutoff = (today - timedelta(days=FLAGGED_DAYS)).isoformat()
    flagged_path.write_bytes(gzip.compress(json.dumps({k: v for k, v in flagged.items() if v >= cutoff}).encode()))
    return rows


def _term(row: dict, tok: str) -> dict:
    try:
        display = _get(f"/users/{row['owner']}", tok).get("name") or ""
    except OSError:
        display = ""
    row["variants"] = variants(row, display)
    gain = f",一天 +{row['delta']}" if row["delta"] is not None else ""
    return {"term": row["variants"][0], "recent": 1, "variants": row["variants"], "repo": row["repo"],
            "note": f"GitHub 爆发 {row['repo']} ★{row['stars']}(均 {row['velocity']}/天{gain})",
            "examples": [f"{row['repo']}: {row['description']}"], "born": row.get("born")}


def breakouts(snapshot_dir: Path) -> dict:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    tok = token()
    repos, late, late_error = searched(tok, date.today())
    path = snapshot_dir / "gh_stars.json.gz"
    before = json.loads(gzip.decompress(path.read_bytes())) if path.exists() else None
    rows = score(repos, before, datetime.now(timezone.utc))
    if repos:
        path.write_bytes(gzip.compress(json.dumps({r["full_name"]: r["stargazers_count"] for r in repos}).encode()))
    rows = mark_new(rows, snapshot_dir / "gh_flagged.json.gz", date.today())
    terms = [_term(row, tok) for row in rows if row["new"]]
    return {"searched": len(repos), "searched_late": late, "late_error": late_error,
            "first_run": before is None, "repos": rows, "terms": terms}
