"""
Daily Report Generator — runs in GitHub Actions or locally.
Queries Supabase for new skills (last 48h) + high momentum projects,
outputs a markdown report to backend/output/.
"""

import os
import json
import datetime
from pathlib import Path

# Try psycopg2 first (CI), fall back to httpx+Supabase REST
try:
    import sqlalchemy
    from sqlalchemy import text
    HAS_DB = True
except ImportError:
    HAS_DB = False

SUPABASE_URL = "https://vknzzecmzsfmohglpfgm.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo"
SITE_URL = os.getenv("SITE_URL", "https://agentskillshub.top")


def fetch_via_rest(cutoff_iso: str):
    """Fetch new skills via Supabase REST API."""
    import httpx

    headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {SUPABASE_ANON_KEY}"}
    base = f"{SUPABASE_URL}/rest/v1/skills"

    # New skills in last 48h, ordered by star gain
    params = {
        "select": "repo_full_name,repo_name,author_name,description,stars,prev_stars,category,score,quality_score,first_seen,created_at,star_momentum",
        "first_seen": f"gte.{cutoff_iso}",
        "stars": "gte.20",
        "order": "star_momentum.desc.nullslast,stars.desc",
        "limit": "50",
    }
    resp = httpx.get(base, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_via_db(cutoff_iso: str):
    """Fetch new skills via direct DB connection."""
    db_url = os.environ["SUPABASE_DB_URL"]
    engine = sqlalchemy.create_engine(db_url)
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT repo_full_name, repo_name, author_name, description,
                   stars, prev_stars, category, score, quality_score,
                   first_seen, created_at, star_momentum
            FROM skills
            WHERE first_seen >= :cutoff AND stars >= 20
            ORDER BY star_momentum DESC NULLS LAST, stars DESC
            LIMIT 50
        """), {"cutoff": cutoff_iso}).fetchall()
    return [dict(r._mapping) for r in rows]


def generate_report(skills: list, today: str) -> str:
    """Generate markdown daily report."""
    lines = [
        f"## 🔥 今日新鲜 Skills 精选 Top 10（{today}）",
        "",
        "由 agentskillshub.top 整理！",
        "",
    ]

    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    top10 = skills[:10]

    for i, s in enumerate(top10):
        name = s.get("repo_full_name", "")
        repo = s.get("repo_name", "")
        desc = (s.get("description") or "")[:80]
        stars = s.get("stars", 0)
        prev = s.get("prev_stars", 0) or 0
        gain = stars - prev
        created = s.get("created_at", "")
        if isinstance(created, datetime.datetime):
            created = created.isoformat()

        # Mark truly new projects (created < 2 weeks ago)
        is_new = False
        if created:
            try:
                ct = datetime.datetime.fromisoformat(str(created).replace("Z", "+00:00"))
                if (datetime.datetime.now(datetime.timezone.utc) - ct).days <= 14:
                    is_new = True
            except Exception:
                pass

        new_badge = "🆕 " if is_new else ""
        gain_str = f"+{gain}" if gain > 0 else str(gain)

        lines.append(f"{emojis[i]} {new_badge}{name}")
        lines.append(f"⭐ {stars:,} | {gain_str}")
        lines.append(f"{desc}")
        lines.append(f"🔗 github.com/{name}")
        lines.append(f"📊 {SITE_URL}/skill/{name}/")
        lines.append("")

    return "\n".join(lines)


def main():
    today = datetime.date.today()
    today_str = today.strftime("%m月%d日")
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=48)).isoformat()

    print(f"Generating daily report for {today}")
    print(f"Cutoff: {cutoff}")

    if HAS_DB and os.getenv("SUPABASE_DB_URL"):
        print("Using direct DB connection")
        skills = fetch_via_db(cutoff)
    else:
        print("Using Supabase REST API")
        skills = fetch_via_rest(cutoff)

    print(f"Found {len(skills)} candidate skills")

    if not skills:
        print("No new skills found, skipping report generation")
        return

    report = generate_report(skills, today_str)

    # Output to file
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    filename = f"daily-report-{today.isoformat()}.md"
    filepath = output_dir / filename
    filepath.write_text(report, encoding="utf-8")
    print(f"Report saved to {filepath}")
    print("---")
    print(report)


if __name__ == "__main__":
    main()
