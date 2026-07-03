"""
Preview the actual HTML email that was sent on a specific Monday.

Reconstructs the newsletter exactly as the runner would have built it on
that date, using the same query logic and template.

Usage:
    python preview_newsletter.py 2026-04-27 > /tmp/newsletter.html
    open /tmp/newsletter.html
"""
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

supabase_url = os.environ.get("SUPABASE_DB_URL", "").strip()
if supabase_url:
    os.environ["DATABASE_URL"] = supabase_url

from app.database import SessionLocal  # noqa: E402
from app.models.skill import Skill, WeeklyTrendingSnapshot  # noqa: E402
from app.services.email_service import _newsletter_email_html  # noqa: E402

from sqlalchemy import desc, func, or_  # noqa: E402


def render_for(send_date: datetime, mode: str = "v1"):
    """Render the newsletter HTML as-of the given send date (UTC).

    mode:
      v1 (default):  current production rule — first_seen in last 7 days, by stars
      strict (v2):   v1 + (star_gain >= 5 AND created_at >= 14 days)
      v3:            v1 + (created_at >= 21 days OR star_gain >= 50)
                     (keeps "old project surging this week", drops "old project just indexed")
    """
    db = SessionLocal()
    try:
        seven_days_ago = send_date - timedelta(days=7)
        bulk_import_cutoff = datetime(2026, 3, 24, 0, 0, 0, tzinfo=timezone.utc)
        first_seen_start = max(seven_days_ago, bulk_import_cutoff)

        q = (
            db.query(Skill)
            .filter(Skill.first_seen >= first_seen_start)
            .filter(Skill.first_seen < send_date)
        )
        if mode == "strict":
            fourteen_days_ago = send_date - timedelta(days=14)
            q = q.filter(
                (Skill.stars - func.coalesce(Skill.prev_stars, 0)) >= 5
            ).filter(Skill.created_at >= fourteen_days_ago)
        elif mode == "v3":
            twenty_one_days_ago = send_date - timedelta(days=21)
            q = q.filter(
                or_(
                    Skill.created_at >= twenty_one_days_ago,
                    (Skill.stars - func.coalesce(Skill.prev_stars, 0)) >= 50,
                )
            )

        new_skills_raw = q.order_by(desc(Skill.stars)).limit(20).all()

        new_skills_data = [
            {
                "repo_name": s.repo_name,
                "repo_full_name": s.repo_full_name,
                "author_name": s.author_name,
                "author_avatar_url": s.author_avatar_url or "",
                "description": s.description or "",
                "stars": s.stars,
                "star_gain": (s.stars - s.prev_stars) if s.prev_stars else 0,
                "repo_url": s.repo_url,
                "category": s.category,
                "created_at": str(s.created_at)[:10] if s.created_at else "",
            }
            for s in new_skills_raw
        ]

        today = send_date.date()
        latest_week = (
            db.query(WeeklyTrendingSnapshot.week_start, WeeklyTrendingSnapshot.week_end)
            .filter(WeeklyTrendingSnapshot.week_end <= today)
            .order_by(desc(WeeklyTrendingSnapshot.week_start))
            .first()
        )

        trending_data = []
        if latest_week:
            week_start, _ = latest_week
            trending_raw = (
                db.query(WeeklyTrendingSnapshot)
                .filter(WeeklyTrendingSnapshot.week_start == week_start)
                .order_by(desc(WeeklyTrendingSnapshot.star_velocity))
                .limit(5)
                .all()
            )
            trending_data = [
                {
                    "repo_name": s.repo_name,
                    "repo_full_name": s.repo_full_name,
                    "author_name": s.author_name,
                    "description": s.description or "",
                    "stars": s.stars,
                    "star_velocity": round(s.star_velocity, 1) if s.star_velocity else 0,
                    "repo_url": s.repo_url,
                }
                for s in trending_raw
            ]

        total_skills = db.query(func.count(Skill.id)).scalar() or 0
        week_end_date = today - timedelta(days=1)
        week_start_date = week_end_date - timedelta(days=6)
        week_period = (
            f"{week_start_date.strftime('%b %-d')} – "
            f"{week_end_date.strftime('%b %-d, %Y')}"
        )

        return _newsletter_email_html(
            new_skills=new_skills_data,
            trending_skills=trending_data,
            total_skills=total_skills,
            week_period=week_period,
            unsubscribe_url="https://agentskillshub.top/unsubscribe?token=PREVIEW",
        )
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python preview_newsletter.py YYYY-MM-DD [--strict|--v3]", file=sys.stderr)
        sys.exit(1)

    send_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    mode = "strict" if "--strict" in sys.argv else ("v3" if "--v3" in sys.argv else "v1")
    print(render_for(send_date, mode=mode))
