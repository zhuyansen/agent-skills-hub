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
from app.models.skill import Skill, Subscriber  # noqa: E402
from app.services.email_service import send_newsletter  # noqa: E402

from sqlalchemy import desc, func  # noqa: E402


def main():
    logger.info("Starting newsletter runner...")

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

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)

        # 2. Get new skills this week (created on GitHub in last 7 days), ordered by stars
        trending_raw = (
            db.query(Skill)
            .filter(Skill.created_at >= week_ago)
            .order_by(desc(Skill.stars))
            .limit(10)
            .all()
        )
        logger.info("Got new-this-week skills: %d", len(trending_raw))

        # If no new skills this week, fall back to top by stars
        if not trending_raw:
            trending_raw = (
                db.query(Skill)
                .filter(Skill.stars > 100)
                .order_by(desc(Skill.stars))
                .limit(10)
                .all()
            )
            logger.info("Fallback: using top stars (no new skills this week)")

        trending_data = [
            {
                "repo_name": s.repo_name,
                "description": s.description or "",
                "stars": s.stars,
                "repo_url": s.repo_url,
                "score": round(s.score, 1) if s.score else 0,
                "category": s.category,
                "star_momentum": s.star_momentum or 0,
            }
            for s in trending_raw
        ]
        logger.info("Got %d trending skills for newsletter", len(trending_data))

        # 3. Stats
        total_skills = db.query(func.count(Skill.id)).scalar() or 0
        new_skills = db.query(Skill).filter(Skill.created_at >= week_ago).count()

        logger.info("Stats: total=%d, new_this_week=%d", total_skills, new_skills)

        # 4. Send!
        result = send_newsletter(
            recipients=recipients,
            trending_skills=trending_data,
            new_skills_count=new_skills,
            total_skills=total_skills,
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
