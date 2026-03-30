"""Test newsletter: send to a single email to preview the new template."""
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

supabase_url = os.environ.get("SUPABASE_DB_URL", "").strip()
if supabase_url:
    os.environ["DATABASE_URL"] = supabase_url

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.skill import Skill, WeeklyTrendingSnapshot  # noqa: E402
from app.services.email_service import send_newsletter  # noqa: E402
from sqlalchemy import desc, func  # noqa: E402


def main():
    test_email = sys.argv[1] if len(sys.argv) > 1 else "757786288@qq.com"
    logger.info("Sending test newsletter to %s", test_email)

    db = SessionLocal()
    now_utc = datetime.now(timezone.utc)

    try:
        # New skills this week
        seven_days_ago = now_utc - timedelta(days=7)
        new_skills_raw = (
            db.query(Skill)
            .filter(Skill.first_seen >= seven_days_ago)
            .filter(Skill.stars >= 20)
            .order_by(desc(Skill.stars - Skill.prev_stars), desc(Skill.stars))
            .limit(20)
            .all()
        )
        logger.info("Found %d new skills", len(new_skills_raw))

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
            }
            for s in new_skills_raw
        ]

        # Top 5 trending
        today = now_utc.date()
        latest_week = (
            db.query(WeeklyTrendingSnapshot.week_start, WeeklyTrendingSnapshot.week_end)
            .filter(WeeklyTrendingSnapshot.week_end <= today)
            .order_by(desc(WeeklyTrendingSnapshot.week_start))
            .first()
        )

        trending_data = []
        if latest_week:
            week_start, week_end = latest_week
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
        week_end_date = today - timedelta(days=1)  # yesterday (Sunday)
        week_start_date = week_end_date - timedelta(days=6)  # last Monday
        week_period = f"{week_start_date.strftime('%b %-d')} – {week_end_date.strftime('%b %-d, %Y')}"

        logger.info("Stats: total=%d, new=%d, trending=%d, period=%s",
                     total_skills, len(new_skills_data), len(trending_data), week_period)

        recipients = [{"email": test_email, "unsubscribe_token": "test-token-123"}]

        result = send_newsletter(
            recipients=recipients,
            new_skills=new_skills_data,
            trending_skills=trending_data,
            total_skills=total_skills,
            week_period=week_period,
        )

        logger.info("Test result: %s", result)

    finally:
        db.close()


if __name__ == "__main__":
    main()
