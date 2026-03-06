"""
GitHub Actions sync runner.
Runs the full sync job, using SUPABASE_DB_URL if available, otherwise SQLite.

Usage:
  cd backend
  python sync_runner.py
"""
import asyncio
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Override DATABASE_URL to use Supabase if available
supabase_url = os.environ.get("SUPABASE_DB_URL")
if supabase_url:
    os.environ["DATABASE_URL"] = supabase_url
    logger.info("Using Supabase PostgreSQL database")
else:
    logger.info("Using local SQLite database")

from app.scheduler.jobs import sync_all_skills  # noqa: E402


def main():
    logger.info("Starting sync runner...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(sync_all_skills())
        logger.info("Sync runner completed successfully")
    except Exception as e:
        logger.exception("Sync runner failed: %s", e)
        sys.exit(1)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
