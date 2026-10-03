"""Radar signal ②b: one new repo taking off on its own, anywhere on GitHub.

github_surge (signals.py) needs five owners using one word, so it sees a wave only once
others copy the idea, days after it started. Strata (Niko1221/Strata) was one repo, born
2026-09-24, at 7.7k stars nine days later; its name was being searched from 9/26 while
no second repo carried it. This signal watches the repo itself.

GitHub search, not the catalog: repos created in the last WINDOW_DAYS with at least
MIN_STARS, two pages. A repo breaks out when it averages VELOCITY_MIN stars a day since
birth, or gained DELTA_MIN since yesterday's snapshot. For the top few the owner's
display name is fetched too, because people search it ("niko strata", not "niko1221").

A repo stays above the bar for days. It becomes a lead term once, the day it first
breaks out (kept in the snapshot for FLAGGED_DAYS); the table lists all of them.
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
VELOCITY_MIN = 200     # stars a day since creation
DELTA_MIN = 400        # stars since yesterday's run
TOP = 15
FLAGGED_DAYS = 30
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


def score(repos: list[dict], before: dict[str, int] | None, now: datetime) -> list[dict]:
    """Repos that break out, fastest first. `repos` items are GitHub search results."""
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
                    "description": (r.get("description") or "")[:120]})
    out.sort(key=lambda x: -max(x["velocity"], x["delta"] or 0))
    return out[:TOP]


def variants(row: dict, display: str) -> list[str]:
    """The ways people end up searching a repo: its name, the owner's handle with it,
    and the owner's display name with it (Strata: 'strata', 'niko1221 strata', 'niko strata')."""
    term = repo_term(row["name"])
    out = [term, f"{row['owner'].lower()} {term}"]
    first = (display or "").split(" ")[0].lower()
    if first and first != row["owner"].lower() and first.isascii() and first.isalpha():
        out.append(f"{first} {term}")
    return out


def breakouts(snapshot_dir: Path) -> dict:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    tok = token()
    since = (date.today() - timedelta(days=WINDOW_DAYS)).isoformat()
    q = urllib.parse.quote(f"created:>={since} stars:>={MIN_STARS}")
    repos: list[dict] = []
    for page in range(1, PAGES + 1):
        items = _get(f"/search/repositories?q={q}&sort=stars&order=desc&per_page=100&page={page}", tok).get("items", [])
        repos += items
        if len(items) < 100:
            break
    path = snapshot_dir / "gh_stars.json.gz"
    before = json.loads(gzip.decompress(path.read_bytes())) if path.exists() else None
    rows = score(repos, before, datetime.now(timezone.utc))
    if repos:
        path.write_bytes(gzip.compress(json.dumps({r["full_name"]: r["stargazers_count"] for r in repos}).encode()))
    flagged_path = snapshot_dir / "gh_flagged.json.gz"
    flagged: dict[str, str] = json.loads(gzip.decompress(flagged_path.read_bytes())) if flagged_path.exists() else {}
    today = date.today().isoformat()
    for row in rows:
        row["new"] = row["repo"] not in flagged
        flagged.setdefault(row["repo"], today)
    cutoff = (date.today() - timedelta(days=FLAGGED_DAYS)).isoformat()
    flagged_path.write_bytes(gzip.compress(json.dumps({k: v for k, v in flagged.items() if v >= cutoff}).encode()))
    terms = []
    for row in (r for r in rows if r["new"]):
        try:
            display = _get(f"/users/{row['owner']}", tok).get("name") or ""
        except OSError:
            display = ""
        row["variants"] = variants(row, display)
        gain = f",一天 +{row['delta']}" if row["delta"] is not None else ""
        terms.append({"term": row["variants"][0], "recent": 1, "variants": row["variants"],
                      "note": f"GitHub 爆发 {row['repo']} ★{row['stars']}(均 {row['velocity']}/天{gain})",
                      "examples": [f"{row['repo']}: {row['description']}"]})
    return {"searched": len(repos), "first_run": before is None, "repos": rows, "terms": terms}
