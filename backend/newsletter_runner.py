"""
GitHub Actions newsletter runner.
Sends weekly newsletter to all verified subscribers.

Usage:
  cd backend
  python newsletter_runner.py
"""
import logging
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Override DATABASE_URL to use Supabase if available
supabase_url = os.environ.get("SUPABASE_DB_URL", "").strip()
database_url = os.environ.get("DATABASE_URL", "").strip()

if supabase_url:
    os.environ["DATABASE_URL"] = supabase_url
    logger.info("Using Supabase PostgreSQL database")
elif database_url:
    logger.info("Using DATABASE_URL: %s", database_url[:30] + "...")
else:
    os.environ.pop("DATABASE_URL", None)
    logger.info("Using default local SQLite database")

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.skill import Skill, Subscriber, WeeklyTrendingSnapshot  # noqa: E402
from app.services.email_service import send_newsletter  # noqa: E402

from sqlalchemy import desc, func  # noqa: E402


def main():
    logger.info("Starting newsletter runner...")

    # Safety: only send on Monday (weekday 0) unless --force flag is passed
    now_utc = datetime.now(timezone.utc)
    force = "--force" in sys.argv
    if now_utc.weekday() != 0 and not force:
        logger.warning("Today is not Monday (weekday=%d). Use --force to override. Exiting.", now_utc.weekday())
        return

    if not settings.resend_api_key:
        logger.error("RESEND_API_KEY not configured. Exiting.")
        sys.exit(1)

    db = SessionLocal()

    try:
        # 1. Get verified, active subscribers
        verified_subs = (
            db.query(Subscriber)
            .filter(Subscriber.is_active == True, Subscriber.verified == True)  # noqa: E712
            .all()
        )

        if not verified_subs:
            logger.info("No verified subscribers found. Nothing to send.")
            return

        # Ensure all have unsubscribe tokens
        for sub in verified_subs:
            if not sub.unsubscribe_token:
                sub.unsubscribe_token = secrets.token_urlsafe(32)
        db.commit()

        recipients = [
            {"email": s.email, "unsubscribe_token": s.unsubscribe_token or ""}
            for s in verified_subs
        ]
        logger.info("Found %d verified subscribers", len(recipients))

        # 2. Get latest week from weekly_trending_snapshots (Star Velocity History)
        latest_week = (
            db.query(WeeklyTrendingSnapshot.week_start, WeeklyTrendingSnapshot.week_end)
            .order_by(desc(WeeklyTrendingSnapshot.week_start))
            .first()
        )

        if not latest_week:
            logger.error("No weekly_trending_snapshots data found. Exiting.")
            return

        week_start, week_end = latest_week
        logger.info("Using week: %s – %s", week_start, week_end)

        trending_raw = (
            db.query(WeeklyTrendingSnapshot)
            .filter(WeeklyTrendingSnapshot.week_start == week_start)
            .order_by(desc(WeeklyTrendingSnapshot.star_velocity))
            .limit(20)
            .all()
        )
        logger.info("Got %d trending skills from Star Velocity History", len(trending_raw))

        trending_data = [
            {
                "rank": s.rank,
                "repo_name": s.repo_name,
                "repo_full_name": s.repo_full_name,
                "author_name": s.author_name,
                "author_avatar_url": s.author_avatar_url or "",
                "description": s.description or "",
                "stars": s.stars,
                "star_velocity": round(s.star_velocity, 1) if s.star_velocity else 0,
                "repo_url": s.repo_url,
                "category": s.category,
            }
            for s in trending_raw
        ]

        # 3. Stats
        total_skills = db.query(func.count(Skill.id)).scalar() or 0

        # Format week period string: "Mar 9 – Mar 15, 2026"
        ws = week_start if isinstance(week_start, datetime) else datetime.fromisoformat(str(week_start))
        we = week_end if isinstance(week_end, datetime) else datetime.fromisoformat(str(week_end))
        week_period = f"{ws.strftime('%b %-d')} – {we.strftime('%b %-d, %Y')}"

        logger.info("Stats: total=%d, week=%s, skills_in_ranking=%d", total_skills, week_period, len(trending_data))

        # 4. Send!
        result = send_newsletter(
            recipients=recipients,
            trending_skills=trending_data,
            total_skills=total_skills,
            week_period=week_period,
        )

        logger.info(
            "Newsletter runner completed: %d sent, %d failed, %d total",
            result["sent"], result["failed"], result["total"],
        )

        if result["failed"] > 0:
            logger.warning("%d emails failed to send", result["failed"])

    except Exception as e:
        logger.exception("Newsletter runner failed: %s", e)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
