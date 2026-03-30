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

        # 2. Get NEW skills this week (first_seen in the last 7 days)
        # Same logic as frontend: order by stars DESC (consistent with website)
        # Exclude bulk import on 2026-03-23 to avoid old high-star repos flooding the list
        seven_days_ago = now_utc - timedelta(days=7)
        bulk_import_cutoff = datetime(2026, 3, 24, 0, 0, 0, tzinfo=timezone.utc)
        first_seen_start = max(seven_days_ago, bulk_import_cutoff)
        new_skills_raw = (
            db.query(Skill)
            .filter(Skill.first_seen >= first_seen_start)
            .order_by(desc(Skill.stars))
            .limit(20)
            .all()
        )
        logger.info("Got %d new skills this week (first_seen >= %s)", len(new_skills_raw), seven_days_ago.date())

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

        # 3. Get Top 5 trending (velocity) for a small highlight section
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

        # 4. Stats
        total_skills = db.query(func.count(Skill.id)).scalar() or 0

        # Format week period string (Mon~Sun = 7 days, end on yesterday)
        week_end_date = today - timedelta(days=1)  # yesterday (Sunday)
        week_start_date = week_end_date - timedelta(days=6)  # last Monday
        week_period = f"{week_start_date.strftime('%b %-d')} – {week_end_date.strftime('%b %-d, %Y')}"

        logger.info("Stats: total=%d, week=%s, new=%d, trending=%d",
                     total_skills, week_period, len(new_skills_data), len(trending_data))

        # 5. Send!
        result = send_newsletter(
            recipients=recipients,
            new_skills=new_skills_data,
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
