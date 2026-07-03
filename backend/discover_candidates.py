#!/usr/bin/env python3
"""
Weekly discovery script for two things:

  1. New master candidates — authors in the skills table who cross the
     "should be a master" thresholds but aren't in skill_masters yet.

  2. New skills from existing masters — repos published by already-verified
     masters that haven't been picked up by our normal sync (e.g. because the
     topic/keywords didn't match our GitHub search queries).

Output (human-readable, for review before acting):
  ops/output/candidates-YYYY-MM-DD.md

Usage:
  cd backend && source venv/bin/activate
  python discover_candidates.py

Reads-only by default. Printing the action plan; user confirms and runs the
generated insert commands manually (or re-runs with --apply to auto-insert).
"""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# ── Config ─────────────────────────────────────────────────────────────

load_dotenv(".env")

SUPABASE = "https://vknzzecmzsfmohglpfgm.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GH_TOKEN = os.getenv("GITHUB_TOKEN")

# Master candidate thresholds — tuned based on 2026-04-21 data where
# authors like alchaincyf had 2,965+ stars but were still missing.
MIN_TOTAL_STARS = 2000
MIN_SKILL_COUNT = 2
RECENT_ACTIVITY_DAYS = 60  # at least one skill pushed within N days

# For existing-master new-repo discovery
MASTER_NEW_REPO_MIN_STARS = 20
MASTER_NEW_REPO_LOOKBACK_DAYS = 90

OUT_DIR = Path(__file__).resolve().parent.parent / "ops" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── HTTP helpers ───────────────────────────────────────────────────────


def sb_get(path: str) -> list[dict[str, Any]] | dict[str, Any]:
    url = f"{SUPABASE}/rest/v1/{path}"
    req = urllib.request.Request(
        urllib.parse.quote(url, safe=":/?=&,.()%*"),
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def gh_get(path: str) -> Any:
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


# ── Feature 1: New master candidates ───────────────────────────────────


def discover_new_master_candidates() -> list[dict[str, Any]]:
    """Find authors who should be masters but aren't."""
    # Pull existing masters' github usernames
    masters = sb_get("skill_masters?select=github&is_active=eq.true&limit=200")
    existing_githubs = {m["github"].lower() for m in masters}

    # Pull ALL skills author aggregates.
    # Use Postgres aggregation via PostgREST: select=author_name,stars but
    # PostgREST doesn't easily do group-by, so we fetch and aggregate in Python.
    skills = []
    offset = 0
    while True:
        page = sb_get(
            f"skills?select=author_name,repo_full_name,stars,last_commit_at,pushed_at&"
            f"stars=gte.100&order=stars.desc&offset={offset}&limit=1000"
        )
        if not page:
            break
        skills.extend(page)
        offset += 1000
        if len(page) < 1000:
            break

    # Aggregate by author
    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    by_author: dict[str, dict[str, Any]] = {}
    for s in skills:
        author = s["author_name"]
        if not author:
            continue
        if author.lower() in existing_githubs:
            continue
        entry = by_author.setdefault(
            author,
            {
                "author": author,
                "total_stars": 0,
                "skills": [],
                "most_recent_push": None,
            },
        )
        entry["total_stars"] += s["stars"] or 0
        entry["skills"].append(s)
        pushed = s.get("pushed_at") or s.get("last_commit_at")
        if pushed:
            try:
                pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
                if pushed_dt.tzinfo is None:
                    pushed_dt = pushed_dt.replace(tzinfo=timezone.utc)
                if (
                    entry["most_recent_push"] is None
                    or pushed_dt > entry["most_recent_push"]
                ):
                    entry["most_recent_push"] = pushed_dt
            except ValueError:
                pass

    # Apply thresholds
    candidates = []
    for author, agg in by_author.items():
        if agg["total_stars"] < MIN_TOTAL_STARS:
            continue
        if len(agg["skills"]) < MIN_SKILL_COUNT:
            continue
        if agg["most_recent_push"] is None or agg["most_recent_push"] < recent_cutoff:
            continue
        # Sort their skills by stars desc
        agg["skills"].sort(key=lambda x: x["stars"], reverse=True)
        candidates.append(agg)

    candidates.sort(key=lambda x: x["total_stars"], reverse=True)
    return candidates


# ── Feature 2: New repos from existing masters ─────────────────────────


def discover_new_skills_from_masters() -> list[dict[str, Any]]:
    """For each master, pull their recent GitHub repos and flag ones missing from our DB."""
    masters = sb_get(
        "skill_masters?select=name,github,x_handle&is_active=eq.true&limit=200"
    )

    lookback = datetime.now(timezone.utc) - timedelta(
        days=MASTER_NEW_REPO_LOOKBACK_DAYS
    )
    findings = []

    for m in masters:
        gh_user = m["github"]
        try:
            repos = gh_get(f"/users/{gh_user}/repos?sort=pushed&per_page=30")
        except Exception as e:
            print(f"  [warn] GitHub fetch failed for {gh_user}: {e}")
            continue

        new_repos = []
        for repo in repos:
            if repo.get("fork") or repo.get("archived"):
                continue
            stars = repo.get("stargazers_count") or 0
            if stars < MASTER_NEW_REPO_MIN_STARS:
                continue
            pushed = repo.get("pushed_at", "")
            try:
                pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
            except ValueError:
                continue
            if pushed_dt < lookback:
                continue

            full_name = repo["full_name"]
            # Check if already in DB
            in_db = sb_get(
                f"skills?select=repo_full_name&repo_full_name=eq.{full_name}&limit=1"
            )
            if in_db:
                continue

            new_repos.append(
                {
                    "full_name": full_name,
                    "stars": stars,
                    "description": repo.get("description") or "",
                    "language": repo.get("language"),
                    "topics": repo.get("topics", []),
                    "pushed_at": pushed[:10],
                    "created_at": repo.get("created_at", "")[:10],
                }
            )

        if new_repos:
            findings.append(
                {
                    "master_name": m["name"],
                    "master_github": gh_user,
                    "master_x": m.get("x_handle"),
                    "new_repos": new_repos,
                }
            )

    return findings


# ── Markdown report ────────────────────────────────────────────────────


def write_report(
    candidates: list[dict[str, Any]], master_news: list[dict[str, Any]]
) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    path = OUT_DIR / f"candidates-{today}.md"

    lines = [
        f"# Master candidates + new master repos — {today}",
        "",
        "Review this file, then run the suggested commands at the end to confirm.",
        "",
    ]

    # ─── Part 1: New master candidates ───
    lines.append(f"## Part 1 — New master candidates ({len(candidates)})")
    lines.append("")
    lines.append(
        f"Criteria: total_stars ≥ {MIN_TOTAL_STARS} · skills ≥ {MIN_SKILL_COUNT} · recent push within {RECENT_ACTIVITY_DAYS} days · not already a master."
    )
    lines.append("")
    if not candidates:
        lines.append("_No new master candidates this round._")
    else:
        for c in candidates:
            recent = (
                c["most_recent_push"].strftime("%Y-%m-%d")
                if c["most_recent_push"]
                else "-"
            )
            lines.append(
                f"### {c['author']} — ⭐{c['total_stars']:,} across {len(c['skills'])} skills (latest push: {recent})"
            )
            lines.append("")
            lines.append(f"- GitHub: https://github.com/{c['author']}")
            lines.append("- Top skills:")
            for s in c["skills"][:5]:
                lines.append(
                    f"  - ⭐{s['stars']:,} · {s['repo_full_name']}"
                )
            lines.append("")
            lines.append("**Add to masters with:**")
            lines.append("```python")
            lines.append(
                f'''# backend/discover_candidates.py --apply "{c['author']}" (or manual:)
master = {{
    'name': '{c['author']}',  # ← fill real name
    'github': '{c['author']}',
    'x_handle': '',  # ← fill X handle if known
    'bio': '',  # ← fill bio (1 sentence)
    'tags': ['claude-skill'],  # ← adjust
    'x_followers': 0,
    'is_active': True,
    'force_verified': True,
}}'''
            )
            lines.append("```")
            lines.append("")

    # ─── Part 2: New repos from existing masters ───
    total_new_from_masters = sum(len(m["new_repos"]) for m in master_news)
    lines.append("")
    lines.append(
        f"## Part 2 — New repos from existing masters ({total_new_from_masters} repos)"
    )
    lines.append("")
    lines.append(
        f"Criteria: master's own repo · stars ≥ {MASTER_NEW_REPO_MIN_STARS} · pushed within {MASTER_NEW_REPO_LOOKBACK_DAYS} days · not yet in DB."
    )
    lines.append("")
    if not master_news:
        lines.append("_No new repos from existing masters found._")
    else:
        for m in master_news:
            lines.append(
                f"### {m['master_name']} (@{m['master_github']}) — {len(m['new_repos'])} new"
            )
            lines.append("")
            for r in m["new_repos"]:
                desc = r["description"][:100] if r["description"] else "(no description)"
                lines.append(
                    f"- **⭐{r['stars']:,}** · `{r['full_name']}` · {r['language']} · pushed {r['pushed_at']}"
                )
                lines.append(f"  - {desc}")
                lines.append(
                    f"  - Add: `python discover_candidates.py --add-repo {r['full_name']}`"
                )
            lines.append("")

    # Write + return
    path.write_text("\n".join(lines))
    return path


# ── Main ───────────────────────────────────────────────────────────────


def main():
    print("🔍 Discovering new master candidates...")
    candidates = discover_new_master_candidates()
    print(f"   Found {len(candidates)} candidates.")

    print("\n🔍 Scanning existing masters for new repos...")
    master_news = discover_new_skills_from_masters()
    print(
        f"   Found {sum(len(m['new_repos']) for m in master_news)} new repos "
        f"across {len(master_news)} masters."
    )

    path = write_report(candidates, master_news)
    print(f"\n📄 Review file written: {path}")
    print("\n👉 Open that file, decide what to approve, then tell me which entries to add.")


if __name__ == "__main__":
    main()
