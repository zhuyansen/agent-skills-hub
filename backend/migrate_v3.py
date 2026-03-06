#!/usr/bin/env python3
"""
Migration v3: Add momentum and README structure columns.
Safe to run multiple times (idempotent).

Run: cd backend && source venv/bin/activate && python migrate_v3.py
"""
import logging
import sqlite3

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from app.config import settings

db_path = settings.database_url.replace("sqlite:///./", "").replace("sqlite:///", "")

NEW_COLUMNS = [
    ("prev_stars", "INTEGER DEFAULT 0"),
    ("star_momentum", "REAL DEFAULT 0.0"),
    ("readme_content", "TEXT DEFAULT NULL"),
    ("readme_structure_score", "REAL DEFAULT 0.0"),
]


def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(skills)")
    existing = {row[1] for row in cursor.fetchall()}

    added = 0
    for col_name, col_def in NEW_COLUMNS:
        if col_name not in existing:
            sql = f"ALTER TABLE skills ADD COLUMN {col_name} {col_def}"
            cursor.execute(sql)
            logger.info("Added column: %s", col_name)
            added += 1
        else:
            logger.info("Column already exists: %s", col_name)

    # Initialize prev_stars from current stars
    cursor.execute("UPDATE skills SET prev_stars = stars WHERE prev_stars = 0 OR prev_stars IS NULL")
    logger.info("Initialized prev_stars from current stars for %d rows", cursor.rowcount)

    conn.commit()
    conn.close()
    logger.info("Migration v3 complete: %d columns added", added)


if __name__ == "__main__":
    migrate()
